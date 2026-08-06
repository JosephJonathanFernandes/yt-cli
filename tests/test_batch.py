"""Tests for batch URL parsing from text, CSV, and JSON sources."""

from __future__ import annotations

import json
from pathlib import Path

from ytdownloader.batch import BatchSummary, parse_csv_file, parse_json_file, parse_lines, parse_text_file


def test_parse_lines_valid_and_invalid():
    text = "https://youtu.be/dQw4w9WgXcQ\nnot a url\n# comment\n\nhttps://www.youtube.com/watch?v=abcdefghijk"
    result = parse_lines(text)
    assert len(result.valid_urls) == 2
    assert len(result.invalid_lines) == 1


def test_parse_text_file(tmp_path: Path):
    path = tmp_path / "urls.txt"
    path.write_text("https://youtu.be/dQw4w9WgXcQ\nbadline\n", encoding="utf-8")
    result = parse_text_file(path)
    assert result.valid_urls == ["https://youtu.be/dQw4w9WgXcQ"]
    assert result.invalid_lines == ["badline"]


def test_parse_csv_file_with_header(tmp_path: Path):
    path = tmp_path / "urls.csv"
    path.write_text("url,notes\nhttps://youtu.be/dQw4w9WgXcQ,first\nbadurl,second\n", encoding="utf-8")
    result = parse_csv_file(path, column="url")
    assert result.valid_urls == ["https://youtu.be/dQw4w9WgXcQ"]
    assert result.invalid_lines == ["badurl"]


def test_parse_json_file_list_of_strings(tmp_path: Path):
    path = tmp_path / "urls.json"
    path.write_text(json.dumps(["https://youtu.be/dQw4w9WgXcQ", "invalid"]), encoding="utf-8")
    result = parse_json_file(path)
    assert result.valid_urls == ["https://youtu.be/dQw4w9WgXcQ"]
    assert result.invalid_lines == ["invalid"]


def test_parse_json_file_list_of_objects(tmp_path: Path):
    path = tmp_path / "urls.json"
    path.write_text(json.dumps({"urls": [{"url": "https://youtu.be/dQw4w9WgXcQ"}]}), encoding="utf-8")
    result = parse_json_file(path)
    assert result.valid_urls == ["https://youtu.be/dQw4w9WgXcQ"]


def test_batch_summary_record():
    summary = BatchSummary()
    summary.record(True)
    summary.record(False, error="boom")
    summary.record(False, skipped=True)
    assert summary.total == 3
    assert summary.succeeded == 1
    assert summary.failed == 1
    assert summary.skipped == 1
    assert summary.errors == ["boom"]
