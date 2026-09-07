import asyncio
from pathlib import Path

import fitz
from fastapi.testclient import TestClient
from pdf2zh_next.host import create_app
from pdf2zh_next.runtime import owner_hash_from_cookie


def make_pdf(path: Path) -> None:
    document = fitz.open()
    document.new_page().insert_text((72, 72), "A small translation test")
    document.save(path)
    document.close()


def test_react_host_bootstrap_and_anonymous_isolation(tmp_path: Path):
    app = create_app(data_dir=tmp_path)
    with TestClient(app) as alice, TestClient(app) as bob:
        page = alice.get("/")
        assert page.status_code == 200
        assert "BilingualPDF" in page.text
        bootstrap = alice.get("/api/bootstrap")
        assert bootstrap.status_code == 200
        payload = bootstrap.json()
        assert payload["default_tier"] == "standard"
        assert payload["tiers"] == [{"slug": "standard", "label": "普通版", "enabled": True}]
        serialized = bootstrap.text.lower()
        assert "minimax" not in serialized
        assert "base_url" not in serialized
        assert "temperature" not in serialized

        alice_cookie = alice.cookies.get("bilingualpdf_session")
        alice_owner = owner_hash_from_cookie(alice_cookie, "dev-session-secret")
        job_id = app.state.history_repo.create_job(
            alice_owner, source_lang="en", target_lang="zh", service="tier",
            config={}, tier_slug="standard", tier_version=1, model_snapshot="hidden-model",
        )
        assert [job["id"] for job in alice.get("/api/jobs").json()] == [job_id]
        assert bob.get("/api/jobs").json() == []
        assert bob.get(f"/api/jobs/{job_id}").status_code == 404

        bob.cookies.set("bilingualpdf_session", alice_cookie + "tampered")
        assert bob.get("/api/jobs").json() == []


def test_upload_contract_does_not_expose_or_persist_key(tmp_path: Path):
    app = create_app(data_dir=tmp_path)

    async def finish_without_translation(owner, job_id, _request, _profile, _files, api_key):
        assert api_key == "request-only-key"
        app.state.history_repo.update_status(owner, job_id, "success")

    app.state.task_manager._run = finish_without_translation
    source = tmp_path / "sample.pdf"
    make_pdf(source)
    with TestClient(app) as client:
        client.get("/api/bootstrap")
        with source.open("rb") as pdf:
            response = client.post(
                "/api/jobs",
                data={"tier": "standard", "source_language": "en", "target_language": "zh"},
                files={"files": ("sample.pdf", pdf, "application/pdf")},
                headers={"X-API-Key": "request-only-key"},
            )
        assert response.status_code == 202
        body = response.json()
        assert "model" not in body
        assert "service" not in body
        assert "config" not in body
        asyncio.run(asyncio.sleep(0))
    database_bytes = (tmp_path / "history.sqlite3").read_bytes()
    assert b"request-only-key" not in database_bytes
    assert b"hidden-model" not in response.content


def test_admin_api_requires_authentication(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("BILINGUALPDF_ADMIN_TOKEN", "local-admin")
    app = create_app(data_dir=tmp_path)
    with TestClient(app) as client:
        assert client.get("/admin/api/tiers").status_code == 401
        assert client.post("/admin/login", json={"username": "admin", "token": "wrong"}).status_code == 401
        assert client.post("/admin/login", json={"username": "admin", "token": "local-admin"}).status_code == 200
        tiers = client.get("/admin/api/tiers")
        assert tiers.status_code == 200
        assert tiers.json()["tiers"][0]["model"] == "MiniMax-M2.7"
