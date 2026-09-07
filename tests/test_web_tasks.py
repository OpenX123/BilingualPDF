import asyncio
from pathlib import Path
from types import SimpleNamespace

from pdf2zh_next.config.translate_engine_model import OpenAISettings
from pdf2zh_next.history import HistoryRepository
from pdf2zh_next.runtime import ConfigRepository
from pdf2zh_next.runtime import TierProfile
from pdf2zh_next.web.schemas import CreateJobRequest
from pdf2zh_next.web.schemas import UploadedDocument
from pdf2zh_next.web.settings_builder import build_translation_settings
from pdf2zh_next.web.tasks import TranslationTaskManager


def test_settings_builder_uses_tier_snapshot_without_gui(tmp_path: Path):
    source = tmp_path / "paper.pdf"
    source.write_bytes(b"%PDF-test")
    profile = TierProfile(
        slug="standard", label="普通版", model="private-model",
        base_url="https://provider.example/v1", timeout=45, temperature=0.1,
        qps=2, workers=3, prompt="Translate precisely", version=8,
    )
    request = CreateJobRequest(source_language="en", target_language="zh", pages="1,3-5")
    settings = build_translation_settings(profile, request, "temporary-key", source, tmp_path)
    assert isinstance(settings.translate_engine_settings, OpenAISettings)
    assert settings.translate_engine_settings.openai_model == "private-model"
    assert settings.translation.lang_in == "en"
    assert settings.translation.lang_out == "zh"
    assert settings.translation.qps == 2
    assert settings.translation.pool_max_workers == 3
    assert settings.pdf.pages == "1,3-5"


def test_public_request_rejects_technical_fields():
    fields = CreateJobRequest.model_fields
    assert set(fields) == {"tier", "source_language", "target_language", "pages"}


def test_task_manager_runs_progress_outputs_and_history(tmp_path: Path, monkeypatch):
    history = HistoryRepository(tmp_path / "history.sqlite3", tmp_path / "tasks")
    config = ConfigRepository(tmp_path / "config.sqlite3")
    manager = TranslationTaskManager(history, config)
    upload = tmp_path / "input.pdf"
    upload.write_bytes(b"%PDF-test")

    async def fake_translate(_settings, input_path):
        yield {"type": "progress_update", "overall_progress": 50, "stage": "排版分析"}
        mono = input_path.parent / "input-mono.pdf"
        dual = input_path.parent / "input-dual.pdf"
        mono.write_bytes(b"mono")
        dual.write_bytes(b"dual")
        result = SimpleNamespace(
            mono_pdf_path=mono,
            dual_pdf_path=dual,
            auto_extracted_glossary_path=None,
        )
        yield {"type": "finish", "translate_result": result, "token_usage": {"main": {"total": 9, "prompt": 6, "completion": 3}}}

    monkeypatch.setattr("pdf2zh_next.web.tasks.do_translate_async_stream", fake_translate)

    async def scenario():
        created = await manager.create(
            "alice", CreateJobRequest(),
            [UploadedDocument(name="input.pdf", path=str(upload), size=9, pages=1)],
            "temporary-key",
        )
        for _ in range(100):
            current = manager.view("alice", created["id"])
            if current["status"] == "success":
                return current
            await asyncio.sleep(0.01)
        raise AssertionError("task did not complete")

    result = asyncio.run(scenario())
    assert result["progress"]["percent"] == 100
    assert result["files"][0]["downloads"]["mono"] is True
    assert result["files"][0]["downloads"]["dual"] is True
    assert result["archives"]["all"] is True
    assert history.get_job("alice", result["id"])["token_total"] == 9
    assert "model" not in result
    history.close()
    config.close()
