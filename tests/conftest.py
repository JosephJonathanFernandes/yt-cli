"""Shared pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from ytdownloader.models import Settings


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    """A Settings instance pointed at a temporary directory."""
    return Settings(
        output_dir=str(tmp_path / "downloads"),
        download_archive_path=str(tmp_path / "archive.txt"),
    )
