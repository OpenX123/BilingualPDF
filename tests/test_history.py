from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pdf2zh_next.history import HistoryRepository
from pdf2zh_next.history import TranslationJob
from pdf2zh_next.history import sanitize_config_snapshot


@pytest.fixture
def repository(tmp_path: Path):
    repo = HistoryRepository(
        db_path=tmp_path / "history.sqlite3",
        output_root=tmp_path / "pdf2zh_files",
    )
    yield repo
    repo.close()


def test_job_lifecycle_and_user_isolation(repository: HistoryRepository):
    job_id = repository.create_job(
        "alice",
        source_lang="English",
        target_lang="Simplified Chinese",
        service="OpenAI",
        config={"lang_from": "English", "openai_api_key": "secret", "qps": 4},
    )
    root = repository.job_directory("alice", job_id)
    input_path = root / "paper.pdf"
    mono_path = root / "paper_mono.pdf"
    dual_path = root / "paper_dual.pdf"
    for path in (input_path, mono_path, dual_path):
        path.write_bytes(b"pdf")

    file_id = repository.add_file(
        "alice",
        job_id,
        original_name="paper.pdf",
        input_path=input_path,
        file_size=3,
        page_count=2,
    )
    repository.update_file(
        "alice",
        job_id,
        file_id,
        status="success",
        mono_path=mono_path,
        dual_path=dual_path,
        token_usage={"main": {"total": 10, "prompt": 7, "completion": 3}},
    )
    zip_path = root / "all_translations.zip"
    zip_path.write_bytes(b"zip")
    repository.record_job_outputs("alice", job_id, zip_path=zip_path)
    repository.update_status("alice", job_id, "success", token_usage={"total": 10})

    job = repository.get_job("alice", job_id)
    assert job["status"] == "success"
    assert job["file_count"] == 1
    assert job["total_pages"] == 2
    assert job["token_total"] == 10
    assert job["config"] == {"lang_from": "English", "qps": 4}
    assert len(repository.list_jobs("alice")) == 1
    assert repository.list_jobs("bob") == []
    with pytest.raises(LookupError):
        repository.get_job("bob", job_id)


def test_record_delete_keeps_files_and_file_delete_is_explicit(repository):
    job_id = repository.create_job(
        "alice",
        source_lang="en",
        target_lang="zh",
        service="OpenAI",
        config={},
    )
    root = repository.job_directory("alice", job_id)
    input_path = root / "paper.pdf"
    input_path.write_bytes(b"pdf")
    repository.add_file("alice", job_id, original_name="paper.pdf", input_path=input_path)

    repository.delete_record("alice", job_id)
    assert repository.list_jobs("alice") == []
    assert input_path.exists()

    job_id_2 = repository.create_job(
        "alice", source_lang="en", target_lang="zh", service="OpenAI", config={}
    )
    root_2 = repository.job_directory("alice", job_id_2)
    file_2 = root_2 / "paper.pdf"
    file_2.write_bytes(b"pdf")
    repository.add_file("alice", job_id_2, original_name="paper.pdf", input_path=file_2)
    repository.delete_files("alice", job_id_2)
    assert not root_2.exists()
    assert repository.get_job("alice", job_id_2)["files"][0]["input_path"] is None
    assert repository.get_job("alice", job_id_2)["files"][0]["status"] == "deleted"


def test_path_guard_and_snapshot_redaction(repository: HistoryRepository):
    job_id = repository.create_job(
        "alice", source_lang="en", target_lang="zh", service="OpenAI", config={}
    )
    outside = repository.output_root / "outside.pdf"
    outside.write_bytes(b"pdf")
    with pytest.raises(PermissionError):
        repository.add_file("alice", job_id, original_name="outside.pdf", input_path=outside)
    with pytest.raises(LookupError):
        repository.resolve_owned_path("bob", job_id, outside)

    snapshot = sanitize_config_snapshot(
        {
            "openai_api_key": "secret",
            "password": "secret",
            "openai_base_url": "https://private.example",
            "custom_url": "https://private.example",
            "server_host": "private.example",
            "service_endpoint": "https://private.example",
            "lang_from": "English",
            "nested": {"token": "secret", "value": 1},
        }
    )
    assert "openai_api_key" not in snapshot
    assert "password" not in snapshot
    assert "openai_base_url" not in snapshot
    assert "custom_url" not in snapshot
    assert "server_host" not in snapshot
    assert "service_endpoint" not in snapshot
    assert snapshot["lang_from"] == "English"
    assert snapshot["nested"] == {"value": 1}


def test_retention_removes_files_then_metadata(repository: HistoryRepository):
    job_id = repository.create_job("alice", source_lang="en", target_lang="zh", service="OpenAI", config={})
    root = repository.job_directory("alice", job_id)
    source = root / "paper.pdf"
    source.write_bytes(b"pdf")
    repository.add_file("alice", job_id, original_name="paper.pdf", input_path=source)
    repository.update_status("alice", job_id, "success")
    old = datetime.now(timezone.utc) - timedelta(days=8)
    TranslationJob.update(created_at=old).where(TranslationJob.job_id == job_id).execute()
    assert repository.cleanup_retention(now=datetime.now(timezone.utc)) == {"files": 1, "jobs": 0}
    assert not root.exists()

    very_old = datetime.now(timezone.utc) - timedelta(days=91)
    TranslationJob.update(created_at=very_old).where(TranslationJob.job_id == job_id).execute()
    result = repository.cleanup_retention(now=datetime.now(timezone.utc))
    assert result["jobs"] == 1
    assert repository.list_jobs("alice") == []
