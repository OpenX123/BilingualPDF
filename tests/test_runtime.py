from pathlib import Path

import pytest

from pdf2zh_next.runtime import ConfigRepository, TierProfile, make_owner_cookie, owner_from_cookie, owner_hash_from_cookie


def test_defaults_and_rollback(tmp_path: Path):
    repo = ConfigRepository(tmp_path / "config.sqlite")
    assert repo.get_profile("standard").model == "MiniMax-M2.7"
    assert repo.get_profile("advanced").enabled is False
    version = repo.save_profile(TierProfile("advanced", "", "example-model", enabled=True))
    assert repo.get_profile("advanced").enabled is True
    repo.rollback("advanced", 1)
    assert repo.get_profile("advanced").enabled is False
    assert version == 2
    assert len(repo.versions("advanced")) == 2
    assert repo.audit_log()[0]["action"] == "rollback"


def test_signed_cookie_rejects_tampering_and_hashes_identity():
    cookie = make_owner_cookie("secret", owner_id="visitor-a")
    assert owner_from_cookie(cookie, "secret") == "visitor-a"
    assert owner_from_cookie(cookie + "x", "secret") is None
    assert owner_from_cookie(cookie, "wrong") is None
    assert owner_hash_from_cookie(cookie, "secret")


def test_advanced_cannot_enable_without_model(tmp_path: Path):
    repo = ConfigRepository(tmp_path / "config.sqlite")
    with pytest.raises(ValueError):
        repo.save_profile(TierProfile("advanced", "", "", enabled=True))
