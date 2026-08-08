"""Batch download support: parsing URL lists from various sources."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from ytdownloader.validators import extract_youtube_urls


@dataclass
class BatchParseResult:
    """Result of parsing a batch of URLs from some source."""

    valid_urls: list[str] = field(default_factory=list)
    invalid_lines: list[str] = field(default_factory=list)

    def dedupe(self) -> "BatchParseResult":
        """Return a copy with duplicate URLs removed, preserving first-seen order."""
        seen: dict[str, None] = {}
        for url in self.valid_urls:
            seen.setdefault(url, None)
        return BatchParseResult(valid_urls=list(seen.keys()), invalid_lines=list(self.invalid_lines))


def parse_lines(text: str) -> BatchParseResult:
    """Parse newline-separated text into valid/invalid URL lists.

    Each line may be a bare URL, or free-form text with a URL embedded in
    it (e.g. "Title - https://youtu.be/xyz"); either form is detected.
    """
    result = BatchParseResult()
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        found = extract_youtube_urls(line)
        if found:
            result.valid_urls.extend(found)
        else:
            result.invalid_lines.append(line)
    return result


def parse_text_file(path: Path) -> BatchParseResult:
    """Parse a plain text file containing one URL (or URL-containing line) per line."""
    content = path.read_text(encoding="utf-8", errors="ignore")
    return parse_lines(content)


def parse_csv_file(path: Path, column: str | None = None) -> BatchParseResult:
    """Parse a CSV file for YouTube URLs.

    If ``column`` is given and matches a header name, only that column is
    scanned. Otherwise every column of every row is scanned automatically,
    so links are found regardless of which column they live in (e.g. a
    "Url" column alongside "Date", "Title", "Channel" columns), and rows
    with no other content on a URL cell are ignored. Rows/cells that
    contain no YouTube link are reported as invalid so nothing silently
    disappears.
    """
    result = BatchParseResult()
    with path.open("r", newline="", encoding="utf-8", errors="ignore") as fh:
        reader = csv.reader(fh)
        rows = list(reader)

    if not rows:
        return result

    header = rows[0]
    has_header = not any(extract_youtube_urls(cell) for cell in header)
    data_rows = rows[1:] if has_header else rows

    col_index: int | None = None
    if column and has_header and column in header:
        col_index = header.index(column)

    for row in data_rows:
        if not row:
            continue
        if col_index is not None:
            cells = [row[col_index]] if col_index < len(row) else []
        else:
            cells = row

        found_in_row: list[str] = []
        for cell in cells:
            found_in_row.extend(extract_youtube_urls(cell))

        if found_in_row:
            result.valid_urls.extend(found_in_row)
        else:
            # Report just the scanned cell(s) when a specific column was
            # requested, or the whole row for context when scanning all
            # columns (since the failing cell isn't known in advance).
            fallback_text = ",".join(c for c in cells if c) if col_index is not None else ",".join(c for c in row if c)
            if fallback_text:
                result.invalid_lines.append(fallback_text)
    return result


def parse_json_file(path: Path) -> BatchParseResult:
    """Parse a JSON file containing a list of URLs, objects with a 'url' key,
    or arbitrary objects/strings that merely contain a YouTube link somewhere.
    """
    result = BatchParseResult()
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("urls", [])
    for item in items:
        if isinstance(item, str):
            candidate_text = item
        elif isinstance(item, dict):
            candidate_text = item.get("url") or " ".join(str(v) for v in item.values())
        else:
            candidate_text = str(item)

        found = extract_youtube_urls(candidate_text)
        if found:
            result.valid_urls.extend(found)
        elif candidate_text.strip():
            result.invalid_lines.append(candidate_text.strip())
    return result


def parse_batch_file(path: Path) -> BatchParseResult:
    """Parse a batch file, dispatching by extension (.txt, .csv, .json).

    Duplicate URLs (the same video listed more than once) are removed
    automatically, keeping the first occurrence.
    """
    suffix = path.suffix.lower()
    if suffix == ".csv":
        result = parse_csv_file(path)
    elif suffix == ".json":
        result = parse_json_file(path)
    else:
        result = parse_text_file(path)
    return result.dedupe()


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
