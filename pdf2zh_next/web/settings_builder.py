"""Build translation-engine settings from a tier snapshot and public inputs."""
from __future__ import annotations

from pathlib import Path

from pdf2zh_next.config.model import SettingsModel
from pdf2zh_next.config.translate_engine_model import OpenAICompatibleSettings
from pdf2zh_next.runtime import TierProfile
from pdf2zh_next.web.schemas import CreateJobRequest


def build_translation_settings(
    profile: TierProfile,
    request: CreateJobRequest,
    api_key: str,
    input_path: Path,
    output_dir: Path,
) -> SettingsModel:
    """Create a validated snapshot without reading or writing GUI configuration."""
    engine = OpenAICompatibleSettings(
        openai_compatible_model=profile.model,
        openai_compatible_base_url=profile.base_url,
        openai_compatible_api_key=api_key,
        openai_compatible_timeout=str(profile.timeout),
        openai_compatible_temperature=str(profile.temperature),
        openai_compatible_reasoning_effort=profile.reasoning_effort or None,
        openai_compatible_send_temperature=True,
        openai_compatible_send_reasoning_effort=bool(profile.reasoning_effort),
        openai_compatible_enable_json_mode=profile.json_mode,
    )
    settings = SettingsModel(translate_engine_settings=engine)
    settings.basic.input_files = {str(input_path)}
    settings.basic.gui = False
    settings.basic.debug = False
    settings.report_interval = 0.2
    settings.translation.lang_in = request.source_language
    settings.translation.lang_out = request.target_language
    settings.translation.output = str(output_dir)
    settings.translation.qps = max(1, int(profile.qps))
    settings.translation.pool_max_workers = max(1, profile.workers)
    settings.translation.custom_system_prompt = profile.prompt or None
    settings.pdf.pages = request.pages
    settings.validate_settings()
    return settings
