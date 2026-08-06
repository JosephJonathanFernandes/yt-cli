"""Playlist analysis, filtering, and batch download orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.progress import Progress

from ytdownloader.audio import download_audio
from ytdownloader.constants import DEFAULT_FILENAME_TEMPLATE, PLAYLIST_FILENAME_TEMPLATE
from ytdownloader.downloader import YTDLPWrapper
from ytdownloader.filters import apply_filters
from ytdownloader.models import (
    DownloadResult,
    PlaylistEntry,
    PlaylistFilters,
    PlaylistInfo,
    Settings,
    VideoInfo,
)
from ytdownloader.video import download_video


def fetch_playlist_info(settings: Settings, url: str) -> PlaylistInfo:
    """Fetch metadata for a playlist without downloading it."""
    wrapper = YTDLPWrapper(settings)
    return wrapper.extract_playlist_info(url)


def filter_playlist_entries(
    playlist: PlaylistInfo, filters: PlaylistFilters
) -> list[PlaylistEntry]:
    """Apply advanced filters to a playlist's entries."""
    return apply_filters(playlist.entries, filters)


def entry_to_video_info(entry: PlaylistEntry) -> VideoInfo:
    """Convert a lightweight :class:`PlaylistEntry` into a :class:`VideoInfo` stub."""
    return VideoInfo(
        id=entry.id or "",
        title=entry.title or "Unknown",
        url=entry.url or "",
        uploader=entry.uploader,
        duration=entry.duration,
        upload_date=entry.upload_date,
        is_live=entry.is_live,
        availability=entry.availability,
    )


def download_playlist_entries(
    settings: Settings,
    entries: list[PlaylistEntry],
    mode: str = "mp4",
    resolution: str = "best",
    bitrate: str = "best",
    output_dir: Optional[Path] = None,
    progress: Optional[Progress] = None,
) -> list[DownloadResult]:
    """Download each selected playlist entry as video or audio.

    ``mode`` is either ``"mp4"`` or ``"mp3"``.
    """
    out_dir = output_dir or Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Use the playlist-numbered template unless the user has explicitly
    # customized the filename template away from the application default.
    template = (
        settings.filename_template
        if settings.filename_template and settings.filename_template != DEFAULT_FILENAME_TEMPLATE
        else PLAYLIST_FILENAME_TEMPLATE
    )

    results: list[DownloadResult] = []
    total = len(entries)
    for position, entry in enumerate(entries, start=1):
        info = entry_to_video_info(entry)
        label = f"Item {position}/{total}: {info.title[:40]}"
        if not info.url:
            results.append(
                DownloadResult(success=False, title=info.title, error_message="Missing URL")
            )
            continue
        if mode == "mp3":
            result = download_audio(
                settings, info, bitrate, out_dir, template, progress, label
            )
        else:
            result = download_video(
                settings, info, resolution, out_dir, template, progress, label
            )
        results.append(result)
    return results
