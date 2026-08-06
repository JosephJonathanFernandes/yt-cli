"""YouTube search functionality."""

from __future__ import annotations

from ytdownloader.downloader import YTDLPWrapper
from ytdownloader.models import Settings, VideoInfo


def search_youtube(settings: Settings, query: str, max_results: int = 10) -> list[VideoInfo]:
    """Search YouTube for videos matching ``query``."""
    wrapper = YTDLPWrapper(settings)
    return wrapper.search(query, max_results)
