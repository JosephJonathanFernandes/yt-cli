"""Low-level JSON persistence helpers.

Centralizes safe read/write of JSON files so config and history modules
don't duplicate file-handling and error-recovery logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ytdownloader.logger import get_logger

logger = get_logger()


def read_json(path: Path, default: Any) -> Any:
    """Read JSON from ``path``, returning ``default`` if missing or corrupt."""
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read JSON file %s: %s", path, exc)
        return default


def write_json(path: Path, data: Any) -> None:
    """Atomically write ``data`` as JSON to ``path``, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=str)
        tmp_path.replace(path)
    except OSError as exc:
        logger.error("Failed to write JSON file %s: %s", path, exc)
        raise
