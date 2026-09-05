"""Persistent translation history for the Gradio application.

The translation cache and user-facing job history have different lifecycles,
so history intentionally lives in its own SQLite database and model set.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import uuid
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

from peewee import AutoField
from peewee import CharField
from peewee import DatabaseProxy
from peewee import DateTimeField
from peewee import ForeignKeyField
from peewee import IntegerField
from peewee import Model
from peewee import SqliteDatabase
from peewee import TextField

from pdf2zh_next.config.translate_engine_model import GUI_PASSWORD_FIELDS
from pdf2zh_next.config.translate_engine_model import GUI_SENSITIVE_FIELDS
from pdf2zh_next.const import DEFAULT_CONFIG_DIR

logger = logging.getLogger(__name__)

_DATA_DIR = os.getenv("BILINGUALPDF_DATA_DIR")
HISTORY_DB_PATH = Path(_DATA_DIR) / "history.sqlite3" if _DATA_DIR else DEFAULT_CONFIG_DIR / "history.v1.sqlite3"
OUTPUT_ROOT = Path(_DATA_DIR) / "tasks" if _DATA_DIR else Path("pdf2zh_files")
_database_proxy = DatabaseProxy()


class _HistoryModel(Model):
    class Meta:
        database = _database_proxy


class TranslationJob(_HistoryModel):
    job_id = CharField(primary_key=True, max_length=64)
    owner_id = CharField(index=True, max_length=255)
    retry_of = CharField(null=True, index=True, max_length=64)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    finished_at = DateTimeField(null=True)
    status = CharField(index=True, max_length=24, default="processing")
    source_lang = CharField(null=True, max_length=32)
    target_lang = CharField(null=True, max_length=32)
    service = CharField(null=True, max_length=128)
    tier_slug = CharField(null=True, index=True, max_length=32)
    tier_version = IntegerField(null=True)
    model_snapshot = CharField(null=True, max_length=256)
    file_count = IntegerField(default=0)
    total_size = IntegerField(default=0)
    total_pages = IntegerField(null=True)
    token_total = IntegerField(default=0)
    token_prompt = IntegerField(default=0)
    token_cache_hit_prompt = IntegerField(default=0)
    token_completion = IntegerField(default=0)
    zip_path = TextField(null=True)
    zip_mono_path = TextField(null=True)
    zip_dual_path = TextField(null=True)
    zip_glossary_path = TextField(null=True)
    config_json = TextField(default="{}")
    error_summary = TextField(null=True)
    deleted_at = DateTimeField(null=True)
    files_deleted_at = DateTimeField(null=True)

    class Meta:
        table_name = "translation_jobs"


class TranslationJobFile(_HistoryModel):
    id = AutoField()
    job = ForeignKeyField(
        TranslationJob,
        backref="files",
        column_name="job_id",
        on_delete="CASCADE",
    )
    original_name = CharField(max_length=512)
    input_path = TextField(null=True)
    mono_path = TextField(null=True)
    dual_path = TextField(null=True)
    glossary_path = TextField(null=True)
    status = CharField(max_length=24, default="processing")
    file_size = IntegerField(default=0)
    page_count = IntegerField(null=True)
    token_total = IntegerField(default=0)
    token_prompt = IntegerField(default=0)
    token_cache_hit_prompt = IntegerField(default=0)
    token_completion = IntegerField(default=0)
    error_summary = TextField(null=True)

    class Meta:
        table_name = "translation_job_files"


_SENSITIVE_NAME_RE = re.compile(
    r"(?:api[_-]?key|password|passwd|secret|token|credential|"
    r"(?:^|[_-])(?:url|host|endpoint)(?:$|[_-]))",
    re.IGNORECASE,
)


def normalize_owner(owner_id: str | None) -> str:
    """Return a stable non-empty owner identifier for history queries."""

    owner = str(owner_id or "").strip()
    return owner or "local"


def owner_hash(owner_id: str | None) -> str:
    """Return a filesystem-safe, non-reversible owner directory name."""

    return hashlib.sha256(normalize_owner(owner_id).encode("utf-8")).hexdigest()[:24]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {
            str(key): safe_config_value(str(key), item)
            for key, item in value.items()
            if safe_config_key(str(key))
        }
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return str(value)


def safe_config_key(key: str) -> bool:
    """Return whether a configuration key is safe to persist in history."""

    lowered = key.lower()
    if key in GUI_PASSWORD_FIELDS or key in GUI_SENSITIVE_FIELDS:
        return False
    if lowered in {"state", "glossary_file", "glossaries"}:
        return False
    return _SENSITIVE_NAME_RE.search(key) is None


def safe_config_value(key: str, value: Any) -> Any:
    if not safe_config_key(key):
        return None
    return _json_safe(value)


def sanitize_config_snapshot(values: dict[str, Any] | None) -> dict[str, Any]:
    """Keep only JSON-safe, non-sensitive UI values for retry."""

    if not values:
        return {}
    snapshot: dict[str, Any] = {}
    for key, value in values.items():
        if not safe_config_key(str(key)):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            snapshot[str(key)] = value
            continue
        if isinstance(value, (list, tuple, set, dict, Path)):
            snapshot[str(key)] = _json_safe(value)
    return snapshot


def _compact_error(error: Any, limit: int = 500) -> str | None:
    if error is None:
        return None
    text = " ".join(str(error).split())
    return text[:limit] or None


def _token_totals(token_usage: dict[str, Any] | None) -> dict[str, int]:
    totals = {"total": 0, "prompt": 0, "cache_hit_prompt": 0, "completion": 0}
    if not isinstance(token_usage, dict):
        return totals
    sources = token_usage.values() if any(isinstance(v, dict) for v in token_usage.values()) else [token_usage]
    for usage in sources:
        if not isinstance(usage, dict):
            continue
        for key in totals:
            try:
                totals[key] += int(usage.get(key, 0) or 0)
            except (TypeError, ValueError):
                continue
    return totals


class HistoryRepository:
    """Thread-safe application-level repository for persistent job history."""

    def __init__(
        self,
        db_path: str | Path = HISTORY_DB_PATH,
        output_root: str | Path = OUTPUT_ROOT,
    ) -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_root = Path(output_root).expanduser().resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)

        database = SqliteDatabase(
            str(self.db_path),
            pragmas={"journal_mode": "wal", "busy_timeout": 5000},
        )
        current = _database_proxy.obj
        if current is not database:
            if current is not None and not current.is_closed():
                current.close()
            _database_proxy.initialize(database)
        self.database = database
        if self.database.is_closed():
            self.database.connect(reuse_if_open=True)
        self.database.create_tables([TranslationJob, TranslationJobFile], safe=True)
        self._ensure_job_columns()

    def _ensure_job_columns(self) -> None:
        """Add fields introduced by later history versions without dropping data."""

        existing = {
            row[1]
            for row in self.database.execute_sql("PRAGMA table_info(translation_jobs)")
        }
        columns = {
            "zip_path": "TEXT",
            "zip_mono_path": "TEXT",
            "zip_dual_path": "TEXT",
            "zip_glossary_path": "TEXT",
            "files_deleted_at": "DATETIME",
            "tier_slug": "VARCHAR(32)",
            "tier_version": "INTEGER",
            "model_snapshot": "VARCHAR(256)",
        }
        for name, definition in columns.items():
            if name not in existing:
                self.database.execute_sql(
                    f"ALTER TABLE translation_jobs ADD COLUMN {name} {definition}"
                )

    def close(self) -> None:
        if not self.database.is_closed():
            self.database.close()

    def job_directory(self, owner_id: str, job_id: str) -> Path:
        if not re.fullmatch(r"[0-9a-fA-F-]{16,64}", job_id):
            raise ValueError("Invalid job id")
        return (self.output_root / owner_hash(owner_id) / job_id).resolve()

    def _assert_owned_job(self, owner_id: str, job_id: str) -> TranslationJob:
        job = TranslationJob.get_or_none(
            (TranslationJob.job_id == job_id)
            & (TranslationJob.owner_id == normalize_owner(owner_id))
            & TranslationJob.deleted_at.is_null(True)
        )
        if job is None:
            raise LookupError("Translation history item not found")
        return job

    def create_job(
        self,
        owner_id: str | None,
        *,
        source_lang: str | None,
        target_lang: str | None,
        service: str | None,
        config: dict[str, Any] | None,
        tier_slug: str | None = None,
        tier_version: int | None = None,
        model_snapshot: str | None = None,
        retry_of: str | None = None,
        job_id: str | None = None,
    ) -> str:
        normalized_owner = normalize_owner(owner_id)
        identifier = job_id or str(uuid.uuid4())
        self.job_directory(normalized_owner, identifier).mkdir(parents=True, exist_ok=True)
        TranslationJob.create(
            job_id=identifier,
            owner_id=normalized_owner,
            retry_of=retry_of,
            source_lang=source_lang,
            target_lang=target_lang,
            service=service,
            tier_slug=tier_slug,
            tier_version=tier_version,
            model_snapshot=model_snapshot,
            config_json=json.dumps(
                sanitize_config_snapshot(config), ensure_ascii=True, sort_keys=True
            ),
        )
        return identifier

    def add_file(
        self,
        owner_id: str | None,
        job_id: str,
        *,
        original_name: str,
        input_path: str | Path | None,
        file_size: int = 0,
        page_count: int | None = None,
    ) -> int:
        job = self._assert_owned_job(owner_id, job_id)
        safe_input = self._validate_job_path(job, input_path)
        record = TranslationJobFile.create(
            job=job,
            original_name=Path(original_name).name,
            input_path=str(safe_input) if safe_input else None,
            file_size=max(0, int(file_size or 0)),
            page_count=page_count,
            status="processing",
        )
        self._refresh_job_counts(job)
        return record.id

    def update_file(
        self,
        owner_id: str | None,
        job_id: str,
        file_id: int,
        *,
        status: str | None = None,
        mono_path: str | Path | None = None,
        dual_path: str | Path | None = None,
        glossary_path: str | Path | None = None,
        token_usage: dict[str, Any] | None = None,
        error: Any = None,
    ) -> None:
        job = self._assert_owned_job(owner_id, job_id)
        record = TranslationJobFile.get_or_none(
            (TranslationJobFile.id == file_id) & (TranslationJobFile.job == job)
        )
        if record is None:
            raise LookupError("Translation history file not found")
        updates: dict[str, Any] = {}
        for field_name, value in (
            ("mono_path", mono_path),
            ("dual_path", dual_path),
            ("glossary_path", glossary_path),
        ):
            if value is not None:
                safe_value = self._validate_job_path(job, value)
                updates[field_name] = str(safe_value) if safe_value else None
        if status is not None:
            updates["status"] = status
        if error is not None:
            updates["error_summary"] = _compact_error(error)
        totals = _token_totals(token_usage)
        if token_usage is not None:
            updates.update(
                token_total=totals["total"],
                token_prompt=totals["prompt"],
                token_cache_hit_prompt=totals["cache_hit_prompt"],
                token_completion=totals["completion"],
            )
        if updates:
            TranslationJobFile.update(**updates).where(
                TranslationJobFile.id == file_id
            ).execute()
        self._refresh_job_counts(job)

    def update_status(
        self,
        owner_id: str | None,
        job_id: str,
        status: str,
        *,
        error: Any = None,
        token_usage: dict[str, Any] | None = None,
    ) -> None:
        job = self._assert_owned_job(owner_id, job_id)
        totals = _token_totals(token_usage)
        values: dict[str, Any] = {
            "status": status,
            "finished_at": (
                datetime.now(timezone.utc)
                if status in {"success", "failed", "cancelled"}
                else None
            ),
        }
        if error is not None:
            values["error_summary"] = _compact_error(error)
        if token_usage is not None:
            values.update(
                token_total=totals["total"],
                token_prompt=totals["prompt"],
                token_cache_hit_prompt=totals["cache_hit_prompt"],
                token_completion=totals["completion"],
            )
        TranslationJob.update(**values).where(TranslationJob.job_id == job.job_id).execute()

    def record_job_outputs(
        self,
        owner_id: str | None,
        job_id: str,
        *,
        zip_path: str | Path | None = None,
        zip_mono_path: str | Path | None = None,
        zip_dual_path: str | Path | None = None,
        zip_glossary_path: str | Path | None = None,
    ) -> None:
        job = self._assert_owned_job(owner_id, job_id)
        values: dict[str, Any] = {}
        for field_name, path in (
            ("zip_path", zip_path),
            ("zip_mono_path", zip_mono_path),
            ("zip_dual_path", zip_dual_path),
            ("zip_glossary_path", zip_glossary_path),
        ):
            if path is not None:
                values[field_name] = str(self._validate_job_path(job, path))
        if values:
            TranslationJob.update(**values).where(
                TranslationJob.job_id == job.job_id
            ).execute()

    def _refresh_job_counts(self, job: TranslationJob) -> None:
        files = list(TranslationJobFile.select().where(TranslationJobFile.job == job))
        totals = {
            "file_count": len(files),
            "total_size": sum(max(0, f.file_size or 0) for f in files),
            "total_pages": sum(f.page_count or 0 for f in files) or None,
            "token_total": sum(f.token_total or 0 for f in files),
            "token_prompt": sum(f.token_prompt or 0 for f in files),
            "token_cache_hit_prompt": sum(f.token_cache_hit_prompt or 0 for f in files),
            "token_completion": sum(f.token_completion or 0 for f in files),
        }
        TranslationJob.update(**totals).where(TranslationJob.job_id == job.job_id).execute()

    def _validate_job_path(
        self, job: TranslationJob, path: str | Path | None
    ) -> Path | None:
        if path is None:
            return None
        candidate = Path(path).expanduser().resolve()
        job_root = self.job_directory(job.owner_id, job.job_id)
        if not candidate.is_relative_to(job_root):
            raise PermissionError("History file path is outside the job directory")
        return candidate

    def resolve_owned_path(
        self, owner_id: str | None, job_id: str, path: str | Path | None
    ) -> Path | None:
        """Validate a stored path against the current user's job directory."""

        job = self._assert_owned_job(owner_id, job_id)
        candidate = self._validate_job_path(job, path)
        if candidate is None or not candidate.exists():
            return None
        return candidate

    @staticmethod
    def _serialize_job(job: TranslationJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "owner_id": job.owner_id,
            "retry_of": job.retry_of,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "status": job.status,
            "source_lang": job.source_lang,
            "target_lang": job.target_lang,
            "service": job.service,
            "tier_slug": job.tier_slug or ("standard" if job.service else None),
            "tier_version": job.tier_version,
            "file_count": job.file_count,
            "total_size": job.total_size,
            "total_pages": job.total_pages,
            "token_total": job.token_total,
            "token_prompt": job.token_prompt,
            "token_cache_hit_prompt": job.token_cache_hit_prompt,
            "token_completion": job.token_completion,
            "zip_path": job.zip_path,
            "zip_mono_path": job.zip_mono_path,
            "zip_dual_path": job.zip_dual_path,
            "zip_glossary_path": job.zip_glossary_path,
            "error_summary": job.error_summary,
            "files_deleted_at": (
                job.files_deleted_at.isoformat() if job.files_deleted_at else None
            ),
            "config": json.loads(job.config_json or "{}"),
            "files": [
                {
                    "id": item.id,
                    "original_name": item.original_name,
                    "input_path": item.input_path,
                    "mono_path": item.mono_path,
                    "dual_path": item.dual_path,
                    "glossary_path": item.glossary_path,
                    "status": item.status,
                    "file_size": item.file_size,
                    "page_count": item.page_count,
                    "error_summary": item.error_summary,
                }
                for item in TranslationJobFile.select().where(
                    TranslationJobFile.job == job
                )
            ],
        }

    def get_job(self, owner_id: str | None, job_id: str) -> dict[str, Any]:
        return self._serialize_job(self._assert_owned_job(owner_id, job_id))

    def list_jobs(
        self,
        owner_id: str | None,
        *,
        search: str | None = None,
        status: str | None = None,
        sort: str = "newest",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = TranslationJob.select().where(
            (TranslationJob.owner_id == normalize_owner(owner_id))
            & TranslationJob.deleted_at.is_null(True)
        )
        if search:
            query = query.where(
                TranslationJob.job_id.in_(
                    TranslationJobFile.select(TranslationJobFile.job)
                    .where(TranslationJobFile.original_name.contains(search))
                )
            )
        if status and status != "all":
            query = query.where(TranslationJob.status == status)
        query = query.order_by(
            TranslationJob.created_at.asc()
            if sort == "oldest"
            else TranslationJob.created_at.desc()
        ).limit(max(1, min(int(limit), 500)))
        return [self._serialize_job(job) for job in query]

    def delete_record(self, owner_id: str | None, job_id: str) -> None:
        job = self._assert_owned_job(owner_id, job_id)
        TranslationJob.update(deleted_at=datetime.now(timezone.utc)).where(
            TranslationJob.job_id == job.job_id
        ).execute()

    def delete_files(self, owner_id: str | None, job_id: str) -> None:
        job = self._assert_owned_job(owner_id, job_id)
        job_root = self.job_directory(job.owner_id, job.job_id)
        if job_root.exists():
            # The root has already been checked against the configured output root.
            shutil.rmtree(job_root)
        TranslationJobFile.update(
            input_path=None,
            mono_path=None,
            dual_path=None,
            glossary_path=None,
            status="deleted",
        ).where(TranslationJobFile.job == job).execute()
        TranslationJob.update(files_deleted_at=datetime.now(timezone.utc)).where(
            TranslationJob.job_id == job.job_id
        ).execute()

    def retry_config(self, owner_id: str | None, job_id: str) -> dict[str, Any]:
        job = self._assert_owned_job(owner_id, job_id)
        result = self._serialize_job(job)
        return {
            "job_id": job.job_id,
            "retry_of": job.job_id,
            "config": result["config"],
            "files": result["files"],
        }

    def admin_summary(self) -> dict[str, int]:
        jobs = list(TranslationJob.select().where(TranslationJob.deleted_at.is_null(True)))
        return {
            "jobs": len(jobs),
            "running": sum(job.status == "processing" for job in jobs),
            "succeeded": sum(job.status == "success" for job in jobs),
            "failed": sum(job.status == "failed" for job in jobs),
            "files": sum(job.file_count or 0 for job in jobs),
            "pages": sum(job.total_pages or 0 for job in jobs),
            "tokens": sum(job.token_total or 0 for job in jobs),
        }

    def recent_failures(self, limit: int = 20) -> list[dict[str, Any]]:
        query = (
            TranslationJob.select()
            .where((TranslationJob.status == "failed") & TranslationJob.deleted_at.is_null(True))
            .order_by(TranslationJob.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
        return [
            {
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "tier": job.tier_slug or "standard",
                "error": _compact_error(job.error_summary),
            }
            for job in query
        ]

    def cleanup_retention(self, *, file_days: int = 7, job_days: int = 90, now: datetime | None = None) -> dict[str, int]:
        """Remove old files first, then old metadata; never touch active jobs."""
        cutoff_files = (now or datetime.now(timezone.utc)).timestamp() - file_days * 86400
        cutoff_jobs = (now or datetime.now(timezone.utc)).timestamp() - job_days * 86400
        files_removed = jobs_removed = 0
        for job in TranslationJob.select().where(TranslationJob.deleted_at.is_null(True)):
            created = job.created_at.timestamp() if job.created_at else 0
            if created < cutoff_files and not job.files_deleted_at and job.status != "processing":
                try:
                    self.delete_files(job.owner_id, job.job_id)
                    files_removed += 1
                except (LookupError, OSError):
                    logger.warning("Unable to clean files for job %s", job.job_id)
            if created < cutoff_jobs and job.status != "processing":
                TranslationJob.update(deleted_at=datetime.now(timezone.utc)).where(TranslationJob.job_id == job.job_id).execute()
                jobs_removed += 1
        return {"files": files_removed, "jobs": jobs_removed}


history_repository = HistoryRepository()


__all__ = [
    "HISTORY_DB_PATH",
    "HistoryRepository",
    "TranslationJob",
    "TranslationJobFile",
    "history_repository",
    "normalize_owner",
    "owner_hash",
    "sanitize_config_snapshot",
]
