"""FastAPI host for the React BilingualPDF application."""
from __future__ import annotations

import asyncio
import contextlib
import hashlib
import hmac
import os
from pathlib import Path

import httpx
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles

from pdf2zh_next.history import HistoryRepository
from pdf2zh_next.runtime import TierProfile
from pdf2zh_next.runtime import get_config_repository
from pdf2zh_next.runtime import make_owner_cookie
from pdf2zh_next.runtime import owner_hash_from_cookie
from pdf2zh_next.runtime import production_secrets_valid
from pdf2zh_next.runtime import validate_admin_token
from pdf2zh_next.web import TranslationTaskManager
from pdf2zh_next.web import create_api_router


class TierUpdate(BaseModel):
    slug: str
    model: str = ""
    base_url: str = "https://api.minimaxi.com/v1"
    timeout: int = 120
    temperature: float = 0.2
    reasoning_effort: str = ""
    json_mode: bool = False
    prompt: str = ""
    qps: float = 1.0
    workers: int = 1
    enabled: bool = False


class TierTest(BaseModel):
    slug: str
    api_key: str


class AdminLogin(BaseModel):
    username: str
    token: str


def create_app(*, data_dir: str | Path | None = None, production: bool = False) -> FastAPI:
    if not production_secrets_valid(production=production):
        raise RuntimeError("BILINGUALPDF_ADMIN_TOKEN and BILINGUALPDF_SESSION_SECRET are required in production")
    root = Path(data_dir or os.getenv("BILINGUALPDF_DATA_DIR", "data")).resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = get_config_repository(str(root))
    history = HistoryRepository(root / "history.sqlite3", root / "tasks")
    manager = TranslationTaskManager(history, config)
    admin_token = os.getenv("BILINGUALPDF_ADMIN_TOKEN", "dev-admin-token")
    session_secret = os.getenv("BILINGUALPDF_SESSION_SECRET", "dev-session-secret")
    admin_cookie = hmac.new(session_secret.encode(), admin_token.encode(), hashlib.sha256).hexdigest()

    app = FastAPI(title="BilingualPDF", docs_url=None, redoc_url=None)
    app.state.config_repo = config
    app.state.history_repo = history
    app.state.task_manager = manager
    basic = HTTPBasic(auto_error=False)

    class SessionCookieMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            cookie = request.cookies.get("bilingualpdf_session")
            owner = owner_hash_from_cookie(cookie or "", session_secret)
            new_cookie = None
            if not owner:
                new_cookie = make_owner_cookie(session_secret)
                owner = owner_hash_from_cookie(new_cookie, session_secret)
            request.state.owner_id = owner
            response = await call_next(request)
            if new_cookie and not request.url.path.startswith("/admin"):
                response.set_cookie(
                    "bilingualpdf_session", new_cookie, max_age=180 * 86400,
                    httponly=True, samesite="lax", secure=production,
                )
            return response

    app.add_middleware(SessionCookieMiddleware)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "BilingualPDF"}

    async def retention_loop() -> None:
        while True:
            history.cleanup_retention(file_days=7, job_days=90)
            await asyncio.sleep(6 * 3600)

    @app.on_event("startup")
    async def startup() -> None:
        history.cleanup_retention(file_days=7, job_days=90)
        app.state.retention_task = asyncio.create_task(retention_loop())

    @app.on_event("shutdown")
    async def shutdown() -> None:
        task = getattr(app.state, "retention_task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        history.close()

    def is_admin(request: Request, credentials: HTTPBasicCredentials | None, header: str | None) -> bool:
        return any((
            validate_admin_token(request.cookies.get("bilingualpdf_admin"), admin_cookie),
            validate_admin_token(header, admin_token),
            bool(credentials and validate_admin_token(credentials.username, "admin") and validate_admin_token(credentials.password, admin_token)),
        ))

    def require_admin(
        request: Request,
        credentials: HTTPBasicCredentials | None = Depends(basic),  # noqa: B008
        x_admin_token: str | None = Header(default=None),
    ) -> None:
        if not is_admin(request, credentials, x_admin_token):
            raise HTTPException(status_code=401, detail="管理员认证失败")

    @app.post("/admin/login")
    def admin_login(login: AdminLogin) -> JSONResponse:
        if not (validate_admin_token(login.username, "admin") and validate_admin_token(login.token, admin_token)):
            raise HTTPException(status_code=401, detail="管理员认证失败")
        response = JSONResponse({"status": "ok"})
        response.set_cookie("bilingualpdf_admin", admin_cookie, max_age=12 * 3600, httponly=True, secure=production, samesite="strict")
        return response

    @app.post("/admin/logout", status_code=204)
    def admin_logout() -> Response:
        response = Response(status_code=204)
        response.delete_cookie("bilingualpdf_admin")
        return response

    @app.get("/admin/api/session")
    def admin_session(_: None = Depends(require_admin)) -> dict[str, bool]:
        return {"authenticated": True}

    @app.get("/admin/api/tiers")
    def tiers(_: None = Depends(require_admin)) -> dict:
        return {
            "default_tier": config.get_setting("default_tier", "standard"),
            "tiers": [profile.__dict__ for profile in config.profiles()],
        }

    @app.post("/admin/api/tiers")
    def save_tier(update: TierUpdate, _: None = Depends(require_admin)) -> dict:
        if update.slug == "advanced" and update.enabled and not config.get_setting(f"tested:{update.slug}:{update.model}", False):
            raise HTTPException(status_code=409, detail="高级版必须使用临时 Key 测试成功后才能启用")
        config.set_setting("provider_base_url", update.base_url)
        try:
            version = config.save_profile(TierProfile(**update.model_dump(), label="", version=0))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"slug": update.slug, "version": version}

    @app.post("/admin/api/default-tier/{slug}")
    def set_default_tier(slug: str, _: None = Depends(require_admin)) -> dict[str, str]:
        try:
            profile = config.get_profile(slug)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="档位不存在") from exc
        if not profile.enabled:
            raise HTTPException(status_code=409, detail="默认档位必须已启用")
        config.set_setting("default_tier", slug)
        return {"default_tier": slug}

    @app.get("/admin/api/tiers/{slug}/versions")
    def versions(slug: str, _: None = Depends(require_admin)) -> list[dict]:
        return config.versions(slug)

    @app.get("/admin/api/audit")
    def audit(_: None = Depends(require_admin)) -> list[dict]:
        return config.audit_log()

    @app.get("/admin/api/usage")
    def usage(_: None = Depends(require_admin)) -> dict:
        return {"summary": history.admin_summary(), "failures": history.recent_failures()}

    @app.post("/admin/api/test")
    async def test_tier(test: TierTest, _: None = Depends(require_admin)) -> dict[str, str]:
        profile = config.get_profile(test.slug)
        if not test.api_key.strip():
            raise HTTPException(status_code=400, detail="请输入临时测试 Key")
        try:
            async with httpx.AsyncClient(timeout=min(profile.timeout, 30)) as client:
                response = await client.post(
                    profile.base_url.rstrip("/") + "/chat/completions",
                    headers={"Authorization": f"Bearer {test.api_key.strip()}"},
                    json={"model": profile.model, "messages": [{"role": "user", "content": "Reply OK"}], "max_tokens": 2},
                )
            response.raise_for_status()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="配置测试失败，请检查 Key、地址和模型") from exc
        config.set_setting(f"tested:{test.slug}:{profile.model}", True)
        return {"status": "ok"}

    @app.post("/admin/api/tiers/{slug}/rollback/{version}")
    def rollback(slug: str, version: int, _: None = Depends(require_admin)) -> dict[str, str]:
        try:
            config.rollback(slug, version)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="配置版本不存在") from exc
        return {"status": "ok"}

    @app.post("/admin/api/cleanup")
    def cleanup(_: None = Depends(require_admin)) -> dict[str, int]:
        return history.cleanup_retention()

    app.include_router(create_api_router(manager, root / "staging"))

    if os.getenv("BILINGUALPDF_ENABLE_LEGACY", "").lower() in {"1", "true", "yes"}:
        import gradio as gr

        from pdf2zh_next.gui import demo
        app = gr.mount_gradio_app(app, demo, path="/legacy")

    frontend = Path(__file__).resolve().parent / "frontend_dist"
    assets = frontend / "assets"
    if assets.exists():
        app.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:  # noqa: ARG001
        index = frontend / "index.html"
        if not index.exists():
            raise HTTPException(status_code=503, detail="React 前端尚未构建，请运行 npm run build")
        return FileResponse(index, media_type="text/html")

    return app


__all__ = ["create_app"]
