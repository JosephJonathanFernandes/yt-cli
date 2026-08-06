"""Persistent download history management."""

from __future__ import annotations

import csv
import uuid
from pathlib import Path
from typing import Any

from ytdownloader.constants import HISTORY_PATH
from ytdownloader.models import HistoryRecord
from ytdownloader.storage import read_json, write_json


class HistoryManager:
    """Manages loading, querying, and mutating the download history."""

    def __init__(self, path: Path = HISTORY_PATH) -> None:
        self.path = path

    def _load_raw(self) -> list[dict[str, Any]]:
        return read_json(self.path, default=[])

    def load_all(self) -> list[HistoryRecord]:
        """Return all history records, most recent first."""
        raw = self._load_raw()
        records = [HistoryRecord(**r) for r in raw]
        return sorted(records, key=lambda r: r.date, reverse=True)

    def add(self, record: HistoryRecord) -> None:
        """Append a new record to the history."""
        raw = self._load_raw()
        if not record.id:
            record.id = str(uuid.uuid4())
        raw.append(record.model_dump())
        write_json(self.path, raw)

    def delete(self, record_id: str) -> bool:
        """Delete a single record by id. Returns True if a record was removed."""
        raw = self._load_raw()
        new_raw = [r for r in raw if r.get("id") != record_id]
        removed = len(new_raw) != len(raw)
        if removed:
            write_json(self.path, new_raw)
        return removed

    def clear(self) -> None:
        """Remove all history records."""
        write_json(self.path, [])

    def search(self, query: str) -> list[HistoryRecord]:
        """Search history by title or URL substring (case-insensitive)."""
        query = query.lower()
        return [
            r
            for r in self.load_all()
            if query in r.title.lower() or query in r.url.lower()
        ]

    def filter_by(
        self,
        type_: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[HistoryRecord]:
        """Filter history records by type, status, and/or date range."""
        records = self.load_all()
        if type_:
            records = [r for r in records if r.type == type_]
        if status:
            records = [r for r in records if r.status == status]
        if date_from:
            records = [r for r in records if r.date >= date_from]
        if date_to:
            records = [r for r in records if r.date <= date_to]
        return records

    def export_json(self, dest: Path) -> None:
        """Export all history records to a JSON file."""
        write_json(dest, [r.model_dump() for r in self.load_all()])

    def export_csv(self, dest: Path) -> None:
        """Export all history records to a CSV file."""
        records = self.load_all()
        dest.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(HistoryRecord.model_fields.keys())
        with dest.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for r in records:
                row = r.model_dump()
                row["tags"] = ";".join(row.get("tags", []))
                writer.writerow(row)


_history_manager: HistoryManager | None = None


def get_history_manager() -> HistoryManager:
    """Return the process-wide :class:`HistoryManager` singleton."""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager
