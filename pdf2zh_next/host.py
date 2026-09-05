"""FastAPI host for the public BilingualPDF service."""
from __future__ import annotations

import asyncio
import contextlib
import html
import os
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from pdf2zh_next.runtime import TierProfile, get_config_repository, production_secrets_valid, validate_admin_token


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


def create_app(*, data_dir: str | Path | None = None, production: bool = False) -> FastAPI:
    if not production_secrets_valid(production=production):
        raise RuntimeError("BILINGUALPDF_ADMIN_TOKEN and BILINGUALPDF_SESSION_SECRET are required in production")
    root = Path(data_dir or os.getenv("BILINGUALPDF_DATA_DIR", "data"))
    root.mkdir(parents=True, exist_ok=True)
    repo = get_config_repository(str(root))
    admin_token = os.getenv("BILINGUALPDF_ADMIN_TOKEN", "dev-admin-token")
    app = FastAPI(title="BilingualPDF", docs_url=None, redoc_url=None)
    app.state.config_repo = repo
    basic = HTTPBasic(auto_error=False)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "BilingualPDF"}

    async def retention_loop() -> None:
        from pdf2zh_next.history import history_repository

        while True:
            history_repository.cleanup_retention(file_days=7, job_days=90)
            await asyncio.sleep(6 * 3600)

    @app.on_event("startup")
    async def start_retention_cleanup() -> None:
        app.state.retention_task = asyncio.create_task(retention_loop())

    @app.on_event("shutdown")
    async def stop_retention_cleanup() -> None:
        task = getattr(app.state, "retention_task", None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    def require_admin(
        credentials: HTTPBasicCredentials | None = Depends(basic),
        x_admin_token: str | None = Header(default=None),
    ) -> None:
        basic_ok = bool(
            credentials
            and validate_admin_token(credentials.username, "admin")
            and validate_admin_token(credentials.password, admin_token)
        )
        if not basic_ok and not validate_admin_token(x_admin_token, admin_token):
            raise HTTPException(
                status_code=401,
                detail="管理员认证失败",
                headers={"WWW-Authenticate": 'Basic realm="BilingualPDF Admin"'},
            )

    @app.get("/admin", response_class=HTMLResponse)
    def admin_page(_: None = Depends(require_admin)) -> str:
        from pdf2zh_next.history import history_repository

        profiles = repo.profiles()
        summary = history_repository.admin_summary()
        cards = "".join(f'''<section><h2>{html.escape(p.label)}</h2><form onsubmit="saveTier(event,'{p.slug}')">
          <label>模型 ID<input name="model" value="{html.escape(p.model, quote=True)}"></label>
          <label>API 地址<input name="base_url" value="{html.escape(p.base_url, quote=True)}"></label>
          <div class="grid"><label>超时<input name="timeout" type="number" value="{p.timeout}"></label><label>Temperature<input name="temperature" type="number" step="0.1" value="{p.temperature}"></label><label>QPS<input name="qps" type="number" step="0.1" value="{p.qps}"></label><label>工作线程<input name="workers" type="number" value="{p.workers}"></label></div>
          <label><input name="enabled" type="checkbox" {'checked' if p.enabled else ''}> 启用（当前版本 {p.version}）</label>
          <button>保存新版本</button></form>
          <form onsubmit="testTier(event,'{p.slug}')"><label>临时测试 Key<input name="api_key" type="password" autocomplete="off"></label><button class="secondary">发送最小测试请求（可能产生费用）</button></form></section>''' for p in profiles)
        return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>BilingualPDF 管理后台</title><style>
        :root{{font-family:system-ui;color:#172033;background:#f4f6f8}}body{{max-width:960px;margin:32px auto;padding:0 20px}}header{{display:flex;justify-content:space-between;align-items:center}}section{{background:white;border:1px solid #d9dee7;border-radius:8px;padding:20px;margin:16px 0}}label{{display:block;margin:12px 0}}input{{box-sizing:border-box;width:100%;min-height:44px;margin-top:6px;padding:9px;border:1px solid #aeb7c5;border-radius:6px}}input[type=checkbox]{{width:auto;min-height:auto}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}button{{min-height:44px;padding:0 16px;border:0;border-radius:6px;background:#d9287a;color:white;font-weight:650;cursor:pointer}}button.secondary{{background:#273449}}#status{{position:sticky;top:8px;padding:12px;background:#172033;color:white;border-radius:6px;display:none}}@media(max-width:600px){{.grid{{grid-template-columns:1fr}}}}</style></head><body><header><div><h1>BilingualPDF 管理后台</h1><p>渠道、档位及运行策略</p></div><a href="/">返回用户端</a></header><div id="status"></div>{cards}<section><h2>维护</h2><button class="secondary" onclick="cleanup()">立即执行保留清理</button></section><script>
        const status=(text,ok=true)=>{{const e=document.querySelector('#status');e.style.display='block';e.style.background=ok?'#18794e':'#b42318';e.textContent=text}};
        async function saveTier(e,slug){{e.preventDefault();const f=new FormData(e.target), body={{slug,model:f.get('model'),base_url:f.get('base_url'),timeout:+f.get('timeout'),temperature:+f.get('temperature'),qps:+f.get('qps'),workers:+f.get('workers'),enabled:f.get('enabled')==='on'}};const r=await fetch('/admin/api/tiers',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});status(r.ok?'配置已保存，刷新后新任务生效':await r.text(),r.ok)}}
        async function testTier(e,slug){{e.preventDefault();const key=new FormData(e.target).get('api_key');const r=await fetch('/admin/api/test',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{slug,api_key:key}})}});status(r.ok?'配置测试成功':await r.text(),r.ok);e.target.reset()}}
        async function cleanup(){{const r=await fetch('/admin/api/cleanup',{{method:'POST'}});status(r.ok?'清理完成：'+JSON.stringify(await r.json()):await r.text(),r.ok)}}
        </script></body></html>'''.replace(
            "<div id=\"status\"></div>",
            f"<div id=\"status\"></div><section><h2>任务概览</h2><div class=\"grid\"><div>任务：{summary['jobs']}</div><div>运行中：{summary['running']}</div><div>成功：{summary['succeeded']}</div><div>失败：{summary['failed']}</div><div>文件：{summary['files']}</div><div>页数：{summary['pages']}</div></div></section>",
        )

    @app.get("/admin/api/tiers")
    def tiers(_: None = Depends(require_admin)) -> list[dict]:
        return [{"slug": p.slug, "label": p.label, "model": p.model, "base_url": p.base_url, "enabled": p.enabled, "version": p.version} for p in repo.profiles()]

    @app.post("/admin/api/tiers")
    def save_tier(update: TierUpdate, _: None = Depends(require_admin)) -> dict:
        if update.slug == "advanced" and update.enabled and not repo.get_setting(f"tested:{update.slug}:{update.model}", False):
            raise HTTPException(status_code=409, detail="高级版必须使用临时 Key 测试成功后才能启用")
        repo.set_setting("provider_base_url", update.base_url)
        version = repo.save_profile(TierProfile(**update.model_dump(), label="", version=0))
        return {"slug": update.slug, "version": version}

    @app.get("/admin/api/tiers/{slug}/versions")
    def versions(slug: str, _: None = Depends(require_admin)) -> list[dict]:
        return repo.versions(slug)

    @app.get("/admin/api/audit")
    def audit(_: None = Depends(require_admin)) -> list[dict]:
        return repo.audit_log()

    @app.get("/admin/api/usage")
    def usage(_: None = Depends(require_admin)) -> dict:
        from pdf2zh_next.history import history_repository
        return {"summary": history_repository.admin_summary(), "failures": history_repository.recent_failures()}

    @app.post("/admin/api/test")
    async def test_tier(test: TierTest, _: None = Depends(require_admin)) -> dict[str, str]:
        profile = repo.get_profile(test.slug)
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
        repo.set_setting(f"tested:{test.slug}:{profile.model}", True)
        return {"status": "ok"}

    @app.post("/admin/api/tiers/{slug}/rollback/{version}")
    def rollback(slug: str, version: int, _: None = Depends(require_admin)) -> dict[str, str]:
        repo.rollback(slug, version)
        return {"status": "ok"}

    @app.post("/admin/api/cleanup")
    def cleanup(_: None = Depends(require_admin)) -> dict[str, int]:
        from pdf2zh_next.history import history_repository
        return history_repository.cleanup_retention()

    # Mounting is intentionally done after admin routes so /admin cannot be
    # swallowed by Gradio's catch-all handler.
    from pdf2zh_next.gui import demo
    import gradio as gr
    from starlette.middleware.base import BaseHTTPMiddleware

    class SessionCookieMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            if request.url.path.startswith("/admin") or request.cookies.get("bilingualpdf_session"):
                return response
            secret = os.getenv("BILINGUALPDF_SESSION_SECRET", "dev-session-secret")
            from pdf2zh_next.runtime import make_owner_cookie
            response.set_cookie("bilingualpdf_session", make_owner_cookie(secret), max_age=180 * 86400, httponly=True, samesite="lax", secure=production)
            return response

    app.add_middleware(SessionCookieMiddleware)
    app = gr.mount_gradio_app(app, demo, path="")
    return app


__all__ = ["create_app"]
