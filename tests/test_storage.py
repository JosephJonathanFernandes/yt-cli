"""Tests for low-level JSON storage helpers."""

from __future__ import annotations

from pathlib import Path

from ytdownloader.storage import read_json, write_json


def test_read_json_returns_default_when_missing(tmp_path: Path):
    assert read_json(tmp_path / "missing.json", default={"a": 1}) == {"a": 1}


def test_read_json_returns_default_when_corrupt(tmp_path: Path):
    bad = tmp_path / "corrupt.json"
    bad.write_text("{not valid json", encoding="utf-8")
    assert read_json(bad, default=[]) == []


def test_write_and_read_json_roundtrip(tmp_path: Path):
    target = tmp_path / "nested" / "data.json"
    payload = {"title": "Test \u2713", "items": [1, 2, 3]}
    write_json(target, payload)
    assert target.exists()
    assert not target.with_suffix(".json.tmp").exists()
    assert read_json(target, default=None) == payload
