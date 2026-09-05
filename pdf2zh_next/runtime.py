"""Runtime configuration, anonymous identity, and retention primitives.

This module deliberately contains no Gradio or translation-engine code.  It is
safe to import from the web host and from tests, and never persists user API
keys.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from functools import lru_cache
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any


TIER_LABELS = {"standard": "普通版", "advanced": "高级版"}


@dataclass(frozen=True)
class TierProfile:
    slug: str
    label: str
    model: str
    base_url: str = "https://api.minimaxi.com/v1"
    timeout: int = 120
    temperature: float = 0.2
    reasoning_effort: str = ""
    json_mode: bool = False
    prompt: str = ""
    qps: float = 1.0
    workers: int = 1
    enabled: bool = True
    version: int = 1

    def public(self) -> dict[str, Any]:
        return {"slug": self.slug, "label": self.label, "enabled": self.enabled}


def default_profiles() -> dict[str, TierProfile]:
    return {
        "standard": TierProfile("standard", TIER_LABELS["standard"], "MiniMax-M2.7"),
        "advanced": TierProfile("advanced", TIER_LABELS["advanced"], "", enabled=False),
    }


class ConfigRepository:
    """Versioned configuration store. API keys are accepted only by callers."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """CREATE TABLE IF NOT EXISTS tier_versions (
                slug TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL,
                created_at REAL NOT NULL, PRIMARY KEY(slug, version));
            CREATE TABLE IF NOT EXISTS tier_current (
                slug TEXT PRIMARY KEY, version INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS runtime_settings (
                key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS admin_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at REAL NOT NULL,
                action TEXT NOT NULL, changes TEXT NOT NULL);
            """
        )
        if not self.db.execute("SELECT 1 FROM tier_current LIMIT 1").fetchone():
            for profile in default_profiles().values():
                self.save_profile(profile, action="bootstrap")
        if self.get_setting("provider_base_url") is None:
            self.set_setting("provider_base_url", "https://api.minimaxi.com/v1")
        self.db.commit()

    def save_profile(self, profile: TierProfile, *, action: str = "save") -> int:
        if profile.slug not in TIER_LABELS:
            raise ValueError("unknown tier")
        if profile.slug == "advanced" and profile.enabled and not profile.model.strip():
            raise ValueError("advanced tier requires a model")
        row = self.db.execute("SELECT COALESCE(MAX(version), 0) FROM tier_versions WHERE slug=?", (profile.slug,)).fetchone()
        version = int(row[0]) + 1
        saved = replace(profile, version=version, label=TIER_LABELS[profile.slug])
        self.db.execute("INSERT INTO tier_versions VALUES (?, ?, ?, ?)", (saved.slug, version, json.dumps(asdict(saved), ensure_ascii=False), time.time()))
        self.db.execute("INSERT INTO tier_current VALUES (?, ?) ON CONFLICT(slug) DO UPDATE SET version=excluded.version", (saved.slug, version))
        self.db.execute("INSERT INTO admin_audit(created_at, action, changes) VALUES (?, ?, ?)", (time.time(), action, json.dumps({"slug": saved.slug, "version": version, "enabled": saved.enabled}, ensure_ascii=False)))
        self.db.commit()
        return version

    def get_profile(self, slug: str) -> TierProfile:
        row = self.db.execute("SELECT v.payload FROM tier_versions v JOIN tier_current c ON c.slug=v.slug AND c.version=v.version WHERE v.slug=?", (slug,)).fetchone()
        if not row:
            raise KeyError(slug)
        profile = TierProfile(**json.loads(row[0]))
        return replace(profile, base_url=self.get_setting("provider_base_url", profile.base_url))

    def profiles(self, *, enabled_only: bool = False) -> list[TierProfile]:
        result = [self.get_profile(slug) for slug in TIER_LABELS]
        return [p for p in result if p.enabled] if enabled_only else result

    def rollback(self, slug: str, version: int) -> None:
        if not self.db.execute("SELECT 1 FROM tier_versions WHERE slug=? AND version=?", (slug, version)).fetchone():
            raise KeyError(f"{slug}:{version}")
        self.db.execute("UPDATE tier_current SET version=? WHERE slug=?", (version, slug))
        self.db.execute("INSERT INTO admin_audit(created_at, action, changes) VALUES (?, ?, ?)", (time.time(), "rollback", json.dumps({"slug": slug, "version": version})))
        self.db.commit()

    def versions(self, slug: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT version, payload, created_at FROM tier_versions WHERE slug=? ORDER BY version DESC",
            (slug,),
        ).fetchall()
        current = self.get_profile(slug).version
        return [
            {
                "version": int(row["version"]),
                "created_at": float(row["created_at"]),
                "current": int(row["version"]) == current,
                "profile": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT created_at, action, changes FROM admin_audit ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        ).fetchall()
        return [
            {"created_at": row["created_at"], "action": row["action"], "changes": json.loads(row["changes"])}
            for row in rows
        ]

    def set_setting(self, key: str, value: Any) -> None:
        self.db.execute("INSERT INTO runtime_settings VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, json.dumps(value)))
        self.db.commit()

    def get_setting(self, key: str, default: Any = None) -> Any:
        row = self.db.execute("SELECT value FROM runtime_settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def close(self) -> None:
        self.db.close()


@lru_cache(maxsize=4)
def get_config_repository(data_dir: str | None = None) -> ConfigRepository:
    root = Path(data_dir or os.getenv("BILINGUALPDF_DATA_DIR", "data"))
    return ConfigRepository(root / "bilingualpdf.sqlite3")


def owner_from_cookie(cookie: str, secret: str) -> str | None:
    try:
        raw, signature = cookie.split(".", 1)
        expected = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(base64.urlsafe_b64encode(expected).decode().rstrip("="), signature):
            return None
        payload = json.loads(base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)))
        if int(payload["exp"]) < int(time.time()):
            return None
        return str(payload["id"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, UnicodeError):
        return None


def make_owner_cookie(secret: str, *, owner_id: str | None = None, max_age: int = 180 * 86400) -> str:
    payload = {"id": owner_id or secrets.token_urlsafe(24), "exp": int(time.time()) + max_age}
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(hmac.new(secret.encode(), raw.encode(), hashlib.sha256).digest()).decode().rstrip("=")
    return f"{raw}.{signature}"


def owner_hash_from_cookie(cookie: str, secret: str) -> str | None:
    owner = owner_from_cookie(cookie, secret)
    return hashlib.sha256(owner.encode()).hexdigest()[:24] if owner else None


def validate_admin_token(candidate: str | None, expected: str | None) -> bool:
    return bool(candidate and expected) and hmac.compare_digest(candidate, expected)


def production_secrets_valid(*, production: bool = True) -> bool:
    if not production:
        return True
    return bool(
        os.getenv("BILINGUALPDF_ADMIN_TOKEN")
        and os.getenv("BILINGUALPDF_SESSION_SECRET")
        and os.getenv("BILINGUALPDF_HTTPS_ENABLED", "").lower() in {"1", "true", "yes"}
    )


__all__ = ["ConfigRepository", "TierProfile", "TIER_LABELS", "default_profiles", "get_config_repository", "make_owner_cookie", "owner_from_cookie", "owner_hash_from_cookie", "validate_admin_token", "production_secrets_valid"]
