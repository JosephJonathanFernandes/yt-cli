"""Batch download support: parsing URL lists from various sources."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from ytdownloader.validators import is_valid_youtube_url, normalize_url


@dataclass
class BatchParseResult:
    """Result of parsing a batch of URLs from some source."""

    valid_urls: list[str] = field(default_factory=list)
    invalid_lines: list[str] = field(default_factory=list)


def parse_lines(text: str) -> BatchParseResult:
    """Parse newline-separated text into valid/invalid URL lists."""
    result = BatchParseResult()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if is_valid_youtube_url(line):
            result.valid_urls.append(normalize_url(line))
        else:
            result.invalid_lines.append(line)
    return result


def parse_text_file(path: Path) -> BatchParseResult:
    """Parse a plain text file containing one URL per line."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    return parse_lines(content)


def parse_csv_file(path: Path, column: str | None = None) -> BatchParseResult:
    """Parse a CSV file for URLs, either from a named column or first cell."""
    result = BatchParseResult()
    with path.open("r", newline="", encoding="utf-8", errors="ignore") as fh:
        reader = csv.reader(fh)
        rows = list(reader)

    if not rows:
        return result

    header = rows[0]
    col_index = 0
    data_rows = rows
    if column and column in header:
        col_index = header.index(column)
        data_rows = rows[1:]
    elif any(is_valid_youtube_url(cell) for cell in header):
        data_rows = rows
    else:
        data_rows = rows[1:]

    for row in data_rows:
        if not row:
            continue
        candidate = row[col_index].strip() if col_index < len(row) else ""
        if is_valid_youtube_url(candidate):
            result.valid_urls.append(normalize_url(candidate))
        elif candidate:
            result.invalid_lines.append(candidate)
    return result


def parse_json_file(path: Path) -> BatchParseResult:
    """Parse a JSON file containing a list of URLs or objects with a 'url' key."""
    result = BatchParseResult()
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("urls", [])
    for item in items:
        candidate = item if isinstance(item, str) else item.get("url", "")
        candidate = (candidate or "").strip()
        if is_valid_youtube_url(candidate):
            result.valid_urls.append(normalize_url(candidate))
        elif candidate:
            result.invalid_lines.append(candidate)
    return result


def parse_batch_file(path: Path) -> BatchParseResult:
    """Parse a batch file, dispatching by extension (.txt, .csv, .json)."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return parse_csv_file(path)
    if suffix == ".json":
        return parse_json_file(path)
    return parse_text_file(path)


@dataclass
class BatchSummary:
    """Summary of a completed batch download run."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def record(self, success: bool, skipped: bool = False, error: str | None = None) -> None:
        """Record the outcome of one batch item."""
        self.total += 1
        if skipped:
            self.skipped += 1
        elif success:
            self.succeeded += 1
        else:
            self.failed += 1
            if error:
                self.errors.append(error)
