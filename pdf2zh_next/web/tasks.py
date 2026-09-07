"""Concurrent translation jobs with a small, UI-independent interface."""
from __future__ import annotations

import asyncio
import contextlib
import logging
import shutil
import zipfile
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from pdf2zh_next.high_level import do_translate_async_stream
from pdf2zh_next.history import HistoryRepository
from pdf2zh_next.runtime import TIER_LABELS
from pdf2zh_next.runtime import ConfigRepository
from pdf2zh_next.web.schemas import CreateJobRequest
from pdf2zh_next.web.schemas import UploadedDocument
from pdf2zh_next.web.settings_builder import build_translation_settings

logger = logging.getLogger(__name__)


@dataclass
class ActiveJob:
    owner: str
    task: asyncio.Task[None]
    progress: dict[str, Any] = field(default_factory=lambda: {
        "percent": 0, "stage": "等待处理", "file_index": 0, "file_count": 0
    })


class TranslationTaskManager:
    """Own task admission, lifecycle, progress and cancellation."""

    def __init__(self, history: HistoryRepository, config: ConfigRepository) -> None:
        self.history = history
        self.config = config
        self._slots = asyncio.Semaphore(4)
        self._active: dict[str, ActiveJob] = {}
        self._lock = asyncio.Lock()

    async def create(
        self,
        owner: str,
        request: CreateJobRequest,
        files: list[UploadedDocument],
        api_key: str,
    ) -> dict[str, Any]:
        if not api_key.strip():
            raise ValueError("请先在设置中填写 API Key")
        profile = self.config.get_profile(request.tier)
        if not profile.enabled:
            raise ValueError("所选翻译档位暂未开放")
        async with self._lock:
            owner_running = sum(job.owner == owner for job in self._active.values())
            if owner_running >= 2:
                raise RuntimeError("当前浏览器已有 2 个任务在运行")
            if len(self._active) >= 54:
                raise RuntimeError("等待队列已满，请稍后重试")
            job_id = self.history.create_job(
                owner,
                source_lang=request.source_language,
                target_lang=request.target_language,
                service="tier",
                config={"tier": request.tier, "pages": request.pages},
                tier_slug=profile.slug,
                tier_version=profile.version,
                model_snapshot=profile.model,
            )
            output_dir = self.history.job_directory(owner, job_id)
            stored: list[UploadedDocument] = []
            for upload in files:
                source = Path(upload.path)
                target = output_dir / source.name
                if source.resolve() != target.resolve():
                    shutil.move(str(source), target)
                stored.append(upload.model_copy(update={"path": str(target)}))
            task = asyncio.create_task(
                self._run(owner, job_id, request, profile, stored, api_key.strip()),
                name=f"translation:{job_id}",
            )
            self._active[job_id] = ActiveJob(
                owner=owner,
                task=task,
                progress={"percent": 0, "stage": "等待处理", "file_index": 0, "file_count": len(stored)},
            )
        return self.view(owner, job_id)

    async def _run(self, owner, job_id, request, profile, files, api_key) -> None:
        current_file_id: int | None = None
        token_totals = {"total": 0, "prompt": 0, "cache_hit_prompt": 0, "completion": 0}
        results: list[dict[str, str | None]] = []
        try:
            async with self._slots:
                self.history.update_status(owner, job_id, "processing")
                for index, upload in enumerate(files, 1):
                    path = Path(upload.path)
                    current_file_id = self.history.add_file(
                        owner, job_id, original_name=upload.name, input_path=path,
                        file_size=upload.size, page_count=upload.pages,
                    )
                    settings = build_translation_settings(profile, request, api_key, path, path.parent)
                    result_paths = {"mono": None, "dual": None, "glossary": None}
                    usage: dict[str, Any] = {}
                    async for event in do_translate_async_stream(settings, path):
                        kind = event.get("type")
                        if kind in {"progress_start", "progress_update", "progress_end"}:
                            inner = float(event.get("overall_progress", 0))
                            percent = round(((index - 1) + inner / 100) / len(files) * 100, 1)
                            self._set_progress(job_id, percent, str(event.get("stage", "处理中")), index, len(files))
                        elif kind == "finish":
                            translated = event["translate_result"]
                            result_paths = {
                                "mono": self._existing(translated.mono_pdf_path),
                                "dual": self._existing(translated.dual_pdf_path),
                                "glossary": self._existing(translated.auto_extracted_glossary_path),
                            }
                            usage = event.get("token_usage") or {}
                            break
                        elif kind == "error":
                            raise RuntimeError(str(event.get("error", "翻译失败")))
                    self.history.update_file(
                        owner, job_id, current_file_id, status="success",
                        mono_path=result_paths["mono"], dual_path=result_paths["dual"],
                        glossary_path=result_paths["glossary"], token_usage=usage,
                    )
                    results.append(result_paths)
                    for source in usage.values():
                        if isinstance(source, dict):
                            for key in token_totals:
                                token_totals[key] += int(source.get(key, 0) or 0)
                archives = self._make_archives(Path(files[0].path).parent, results)
                self.history.record_job_outputs(owner, job_id, **archives)
                self.history.update_status(owner, job_id, "success", token_usage=token_totals)
                self._set_progress(job_id, 100, "翻译完成", len(files), len(files))
        except asyncio.CancelledError:
            if current_file_id is not None:
                with contextlib.suppress(Exception):
                    self.history.update_file(owner, job_id, current_file_id, status="cancelled")
            with contextlib.suppress(Exception):
                self.history.update_status(owner, job_id, "cancelled")
            raise
        except Exception as exc:
            logger.exception("Translation job %s failed", job_id)
            if current_file_id is not None:
                with contextlib.suppress(Exception):
                    self.history.update_file(owner, job_id, current_file_id, status="failed", error=exc)
            with contextlib.suppress(Exception):
                self.history.update_status(owner, job_id, "failed", error=exc)
            self._set_progress(job_id, self._active[job_id].progress["percent"], "翻译失败", 0, len(files))
        finally:
            # The key is referenced only by this coroutine and becomes collectible here.
            api_key = ""
            await asyncio.sleep(1)
            async with self._lock:
                self._active.pop(job_id, None)

    @staticmethod
    def _existing(value: Any) -> str | None:
        path = Path(value) if value else None
        return str(path) if path and path.exists() else None

    @staticmethod
    def _make_archives(output_dir: Path, results: list[dict[str, str | None]]) -> dict[str, Path | None]:
        definitions = {
            "zip_path": ("all_translations.zip", ("mono", "dual", "glossary")),
            "zip_mono_path": ("all_mono_translations.zip", ("mono",)),
            "zip_dual_path": ("all_dual_translations.zip", ("dual",)),
            "zip_glossary_path": ("all_glossaries.zip", ("glossary",)),
        }
        archives: dict[str, Path | None] = {}
        for field_name, (filename, kinds) in definitions.items():
            entries = [(kind, item[kind]) for item in results for kind in kinds if item.get(kind)]
            if not entries:
                archives[field_name] = None
                continue
            archive = output_dir / filename
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                for kind, value in entries:
                    path = Path(value)
                    bundle.write(path, arcname=f"{kind}_{path.name}")
            archives[field_name] = archive
        return archives

    def _set_progress(self, job_id: str, percent: float, stage: str, index: int, total: int) -> None:
        active = self._active.get(job_id)
        if active:
            active.progress = {"percent": percent, "stage": stage, "file_index": index, "file_count": total}

    def view(self, owner: str, job_id: str) -> dict[str, Any]:
        job = self.history.get_job(owner, job_id)
        active = self._active.get(job_id)
        return self._public_job(job, active.progress if active else None)

    def list(self, owner: str, **filters: Any) -> list[dict[str, Any]]:
        return [self._public_job(job, self._active.get(job["job_id"]).progress if job["job_id"] in self._active else None) for job in self.history.list_jobs(owner, **filters)]

    async def cancel(self, owner: str, job_id: str) -> None:
        self.history.get_job(owner, job_id)
        active = self._active.get(job_id)
        if not active or active.owner != owner:
            raise LookupError("任务已结束或不存在")
        active.task.cancel()

    @staticmethod
    def _public_job(job: dict[str, Any], progress: dict[str, Any] | None) -> dict[str, Any]:
        def file_view(item: dict[str, Any]) -> dict[str, Any]:
            return {
                "id": item["id"], "name": item["original_name"], "status": item["status"],
                "size": item["file_size"], "pages": item["page_count"],
                "downloads": {kind: bool(item.get(f"{kind}_path")) for kind in ("input", "mono", "dual", "glossary")},
            }
        return {
            "id": job["job_id"], "created_at": job["created_at"], "finished_at": job["finished_at"],
            "status": job["status"], "tier": job.get("tier_slug") or "standard",
            "tier_label": TIER_LABELS.get(job.get("tier_slug") or "standard", "普通版"),
            "source_language": job["source_lang"], "target_language": job["target_lang"],
            "file_count": job["file_count"], "total_size": job["total_size"], "total_pages": job["total_pages"],
            "progress": progress or ({"percent": 100, "stage": "翻译完成"} if job["status"] == "success" else None),
            "files": [file_view(item) for item in job["files"]],
            "archives": {kind: bool(job.get(f"zip_{kind}_path" if kind != "all" else "zip_path")) for kind in ("all", "mono", "dual", "glossary")},
            "error": job.get("error_summary"),
        }
