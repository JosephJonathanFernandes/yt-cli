"""Tests for settings loading, saving, updating, resetting, and validation."""

from __future__ import annotations

from pathlib import Path

from ytdownloader.config import ConfigManager
from ytdownloader.exceptions import ConfigError
from ytdownloader.models import Settings

import pytest


def test_load_creates_default_when_missing(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "config.json")
    settings = manager.load()
    assert isinstance(settings, Settings)
    assert (tmp_path / "config.json").exists()


def test_save_and_reload_roundtrip(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "config.json")
    settings = manager.load()
    settings.concurrent_downloads = 5
    manager.save(settings)

    manager2 = ConfigManager(path=tmp_path / "config.json")
    reloaded = manager2.load()
    assert reloaded.concurrent_downloads == 5


def test_update_persists_field(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "config.json")
    manager.load()
    updated = manager.update(retry_attempts=7)
    assert updated.retry_attempts == 7

    manager2 = ConfigManager(path=tmp_path / "config.json")
    assert manager2.load().retry_attempts == 7


def test_update_invalid_value_raises(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "config.json")
    manager.load()
    with pytest.raises(ConfigError):
        manager.update(concurrent_downloads=999)  # exceeds le=10


def test_reset_restores_defaults(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "config.json")
    manager.load()
    manager.update(retry_attempts=9)
    defaults = manager.reset()
    assert defaults.retry_attempts == Settings().retry_attempts


def test_corrupt_config_falls_back_to_defaults(tmp_path: Path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"concurrent_downloads": "not_a_number_but_string_ok"}', encoding="utf-8")
    manager = ConfigManager(path=config_path)
    settings = manager.load()
    assert isinstance(settings, Settings)


def test_export_and_import(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "config.json")
    manager.load()
    manager.update(retry_attempts=4)
    export_path = tmp_path / "exported.json"
    manager.export(export_path)

    manager2 = ConfigManager(path=tmp_path / "other_config.json")
    imported = manager2.import_from(export_path)
    assert imported.retry_attempts == 4


def test_validate_integrity_valid(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "config.json")
    manager.load()
    valid, error = manager.validate_integrity()
    assert valid is True
    assert error is None


def test_validate_integrity_missing_file(tmp_path: Path):
    manager = ConfigManager(path=tmp_path / "nonexistent.json")
    valid, error = manager.validate_integrity()
    assert valid is False
    assert error is not None
