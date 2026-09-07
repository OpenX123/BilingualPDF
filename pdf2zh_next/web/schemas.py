"""Stable public contracts used by the React client."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


class CreateJobRequest(BaseModel):
    tier: str = "standard"
    source_language: str = "en"
    target_language: str = "zh"
    pages: str | None = None

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, value: str) -> str:
        if value not in {"standard", "advanced"}:
            raise ValueError("未知翻译档位")
        return value

    @field_validator("source_language", "target_language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 16:
            raise ValueError("语言代码无效")
        return value

    @field_validator("pages")
    @classmethod
    def validate_pages(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        if len(value) > 200 or any(ch not in "0123456789,- " for ch in value):
            raise ValueError("页码格式无效，请使用 1,3-5")
        return value.replace(" ", "")


class UploadedDocument(BaseModel):
    name: str
    path: str
    size: int = Field(ge=1)
    pages: int | None = Field(default=None, ge=1)
