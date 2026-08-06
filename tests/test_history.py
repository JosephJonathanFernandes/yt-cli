"""Tests for the download history manager."""

from __future__ import annotations

from pathlib import Path

from ytdownloader.history import HistoryManager
from ytdownloader.models import HistoryRecord


def make_record(**kwargs) -> HistoryRecord:
    defaults = dict(
        id="", title="My Video", url="https://youtu.be/abc",
        type="video", status="success",
    )
    defaults.update(kwargs)
    return HistoryRecord(**defaults)


def test_add_and_load_all(tmp_path: Path):
    hm = HistoryManager(path=tmp_path / "history.json")
    hm.add(make_record(id="1"))
    hm.add(make_record(id="2", title="Second"))
    records = hm.load_all()
    assert len(records) == 2


def test_delete_record(tmp_path: Path):
    hm = HistoryManager(path=tmp_path / "history.json")
    hm.add(make_record(id="1"))
    assert hm.delete("1") is True
    assert hm.load_all() == []
    assert hm.delete("missing") is False


def test_clear_history(tmp_path: Path):
    hm = HistoryManager(path=tmp_path / "history.json")
    hm.add(make_record(id="1"))
    hm.add(make_record(id="2"))
    hm.clear()
    assert hm.load_all() == []


def test_search_by_title_and_url(tmp_path: Path):
    hm = HistoryManager(path=tmp_path / "history.json")
    hm.add(make_record(id="1", title="Python Tutorial"))
    hm.add(make_record(id="2", title="Cooking Show"))
    results = hm.search("python")
    assert len(results) == 1
    assert results[0].title == "Python Tutorial"


def test_filter_by_type_and_status(tmp_path: Path):
    hm = HistoryManager(path=tmp_path / "history.json")
    hm.add(make_record(id="1", type="video", status="success"))
    hm.add(make_record(id="2", type="audio", status="failed"))
    assert len(hm.filter_by(type_="video")) == 1
    assert len(hm.filter_by(status="failed")) == 1
    assert len(hm.filter_by(type_="video", status="failed")) == 0


def test_export_json_and_csv(tmp_path: Path):
    hm = HistoryManager(path=tmp_path / "history.json")
    hm.add(make_record(id="1"))
    json_path = tmp_path / "out.json"
    csv_path = tmp_path / "out.csv"
    hm.export_json(json_path)
    hm.export_csv(csv_path)
    assert json_path.exists()
    assert csv_path.exists()
    assert "My Video" in csv_path.read_text(encoding="utf-8")
