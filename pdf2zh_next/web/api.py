"""FastAPI routes consumed by the React single-page application."""
from __future__ import annotations

import asyncio
import json
import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Form
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi import UploadFile
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from pdf2zh_next.i18n import LANGUAGES
from pdf2zh_next.web.schemas import CreateJobRequest
from pdf2zh_next.web.schemas import UploadedDocument
from pdf2zh_next.web.tasks import TranslationTaskManager

MAX_FILES = 10
MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_PAGES = 800


def _page_count(path: Path) -> int | None:
    try:
        import fitz

        with fitz.open(path) as document:
            return document.page_count
    except Exception as exc:
        raise ValueError("无法读取 PDF，请确认文件未损坏") from exc


def _owner(request: Request) -> str:
    owner = getattr(request.state, "owner_id", None)
    if not owner:
        raise HTTPException(status_code=401, detail="匿名会话无效，请刷新页面")
    return owner


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail="任务不存在或不属于当前浏览器")


def create_api_router(manager: TranslationTaskManager, staging_root: Path) -> APIRouter:
    router = APIRouter(prefix="/api")
    staging_root.mkdir(parents=True, exist_ok=True)

    @router.get("/bootstrap")
    def bootstrap() -> dict:
        profiles = manager.config.profiles(enabled_only=True)
        default = manager.config.get_setting("default_tier", "standard")
        enabled = {profile.slug for profile in profiles}
        if default not in enabled:
            default = "standard"
        return {
            "tiers": [profile.public() for profile in profiles],
            "default_tier": default,
            "languages": [{"label": label, "value": code} for label, code in LANGUAGES],
            "limits": {"files": MAX_FILES, "file_mb": 100, "pages": MAX_PAGES, "visitor_jobs": 2},
            "retention": {"files_days": 7, "history_days": 90},
        }

    @router.post("/jobs", status_code=202)
    async def create_job(
        files: Annotated[list[UploadFile], File()],
        owner: Annotated[str, Depends(_owner)],
        tier: Annotated[str, Form()] = "standard",
        source_language: Annotated[str, Form()] = "en",
        target_language: Annotated[str, Form()] = "zh",
        pages: Annotated[str | None, Form()] = None,
        api_key: str | None = Header(default=None, alias="X-API-Key"),
    ) -> dict:
        if not files or len(files) > MAX_FILES:
            raise HTTPException(status_code=413, detail=f"每次最多上传 {MAX_FILES} 个 PDF")
        try:
            job_request = CreateJobRequest(
                tier=tier, source_language=source_language,
                target_language=target_language, pages=pages,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="翻译参数无效") from exc
        stage = Path(tempfile.mkdtemp(prefix="upload-", dir=staging_root))
        uploaded: list[UploadedDocument] = []
        used_names: set[str] = set()
        try:
            for index, upload in enumerate(files, 1):
                original = Path(upload.filename or f"document-{index}.pdf").name
                if Path(original).suffix.lower() != ".pdf":
                    raise HTTPException(status_code=415, detail=f"{original} 不是 PDF 文件")
                name = original
                counter = 2
                while name.lower() in used_names:
                    name = f"{Path(original).stem}-{counter}.pdf"
                    counter += 1
                used_names.add(name.lower())
                target = stage / name
                size = 0
                with target.open("wb") as output:
                    while chunk := await upload.read(1024 * 1024):
                        size += len(chunk)
                        if size > MAX_FILE_BYTES:
                            raise HTTPException(status_code=413, detail=f"{original} 超过 100 MB")
                        output.write(chunk)
                with target.open("rb") as uploaded_pdf:
                    signature = uploaded_pdf.read(5)
                if size < 5 or signature != b"%PDF-":
                    raise HTTPException(status_code=415, detail=f"{original} 不是有效 PDF")
                page_count = _page_count(target)
                if page_count and page_count > MAX_PAGES:
                    raise HTTPException(status_code=413, detail=f"{original} 超过 800 页")
                uploaded.append(UploadedDocument(name=original, path=str(target), size=size, pages=page_count))
            try:
                return await manager.create(owner, job_request, uploaded, api_key or "")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except RuntimeError as exc:
                raise HTTPException(status_code=429, detail=str(exc)) from exc
        finally:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)

    @router.get("/jobs")
    def list_jobs(
        search: str | None = None,
        status: str | None = None,
        sort: str = "newest",
        owner: str = Depends(_owner),
    ) -> list[dict]:
        return manager.list(owner, search=search, status=status, sort=sort)

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str, owner: str = Depends(_owner)) -> dict:
        try:
            return manager.view(owner, job_id)
        except (LookupError, ValueError) as exc:
            raise _not_found() from exc

    @router.get("/jobs/{job_id}/events")
    def job_events(job_id: str, owner: str = Depends(_owner)) -> EventSourceResponse:
        async def events():
            previous = ""
            while True:
                try:
                    view = manager.view(owner, job_id)
                except (LookupError, ValueError):
                    yield {"event": "error", "data": json.dumps({"detail": "任务不存在"}, ensure_ascii=False)}
                    return
                encoded = json.dumps(view, ensure_ascii=False)
                if encoded != previous:
                    yield {"event": "job", "data": encoded}
                    previous = encoded
                if view["status"] in {"success", "failed", "cancelled"}:
                    return
                await asyncio.sleep(0.75)
        return EventSourceResponse(events())

    @router.post("/jobs/{job_id}/cancel", status_code=202)
    async def cancel_job(job_id: str, owner: str = Depends(_owner)) -> dict[str, str]:
        try:
            await manager.cancel(owner, job_id)
        except (LookupError, ValueError) as exc:
            raise _not_found() from exc
        return {"status": "cancelling"}

    @router.delete("/jobs/{job_id}", status_code=204)
    def delete_job(job_id: str, owner: str = Depends(_owner)) -> None:
        try:
            manager.history.delete_record(owner, job_id)
        except (LookupError, ValueError) as exc:
            raise _not_found() from exc

    @router.delete("/jobs/{job_id}/files", status_code=204)
    def delete_job_files(job_id: str, owner: str = Depends(_owner)) -> None:
        try:
            manager.history.delete_files(owner, job_id)
        except (LookupError, ValueError) as exc:
            raise _not_found() from exc

    @router.get("/jobs/{job_id}/files/{file_id}/{kind}")
    def download_file(job_id: str, file_id: int, kind: str, owner: str = Depends(_owner)) -> FileResponse:
        if kind not in {"input", "mono", "dual", "glossary"}:
            raise HTTPException(status_code=404, detail="文件不存在")
        try:
            job = manager.history.get_job(owner, job_id)
            record = next((item for item in job["files"] if item["id"] == file_id), None)
            if not record or not record.get(f"{kind}_path"):
                raise LookupError
            path = manager.history.resolve_owned_path(owner, job_id, record[f"{kind}_path"])
        except (LookupError, ValueError, PermissionError) as exc:
            raise _not_found() from exc
        return FileResponse(path, filename=Path(path).name, media_type="application/pdf" if path.suffix.lower() == ".pdf" else None)

    @router.get("/jobs/{job_id}/archives/{kind}")
    def download_archive(job_id: str, kind: str, owner: str = Depends(_owner)) -> FileResponse:
        fields = {"all": "zip_path", "mono": "zip_mono_path", "dual": "zip_dual_path", "glossary": "zip_glossary_path"}
        if kind not in fields:
            raise HTTPException(status_code=404, detail="压缩包不存在")
        try:
            job = manager.history.get_job(owner, job_id)
            value = job.get(fields[kind])
            if not value:
                raise LookupError
            path = manager.history.resolve_owned_path(owner, job_id, value)
        except (LookupError, ValueError, PermissionError) as exc:
            raise _not_found() from exc
        return FileResponse(path, filename=path.name, media_type="application/zip")

    return router
