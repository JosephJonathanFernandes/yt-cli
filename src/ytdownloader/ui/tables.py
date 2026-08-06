"""Reusable Rich table builders for videos, playlists, history, and search."""

from __future__ import annotations

from rich.table import Table

from ytdownloader.models import FormatInfo, HistoryRecord, PlaylistEntry, VideoInfo
from ytdownloader.utils import format_duration, format_filesize, format_upload_date


def video_details_table(info: VideoInfo) -> Table:
    """Build a details table for a single video's metadata."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="info", no_wrap=True)
    table.add_column("Value")

    table.add_row("Title", info.title)
    table.add_row("Channel", info.uploader or "Unknown")
    table.add_row("Duration", format_duration(info.duration))
    table.add_row("Views", f"{info.view_count:,}" if info.view_count else "Unknown")
    table.add_row("Uploaded", format_upload_date(info.upload_date))
    if info.description:
        preview = info.description.strip().splitlines()[0][:120] if info.description else ""
        table.add_row("Description", preview + ("..." if len(preview) == 120 else ""))
    table.add_row("Thumbnail", info.thumbnail or "None")
    status_bits = []
    if info.is_live:
        status_bits.append("LIVE")
    if info.is_upcoming:
        status_bits.append("PREMIERE/UPCOMING")
    if info.age_limit:
        status_bits.append(f"Age {info.age_limit}+")
    table.add_row("Status", ", ".join(status_bits) if status_bits else "Normal")
    return table


def formats_table(formats: list[FormatInfo]) -> Table:
    """Build a table listing available formats for a video."""
    table = Table(title="Available Formats")
    table.add_column("Format ID", style="muted")
    table.add_column("Ext")
    table.add_column("Resolution")
    table.add_column("FPS")
    table.add_column("Size")
    table.add_column("Video Codec")
    table.add_column("Audio Codec")

    for f in formats:
        table.add_row(
            f.format_id,
            f.ext,
            f.resolution or (f"{f.height}p" if f.height else "-"),
            str(int(f.fps)) if f.fps else "-",
            format_filesize(f.filesize),
            f.vcodec or "-",
            f.acodec or "-",
        )
    return table


def playlist_entries_table(entries: list[PlaylistEntry], limit: int = 50) -> Table:
    """Build a table listing playlist entries (truncated to ``limit`` rows)."""
    table = Table(title=f"Playlist Entries ({len(entries)} total)")
    table.add_column("#", style="menu.number", justify="right")
    table.add_column("Title")
    table.add_column("Uploader")
    table.add_column("Duration")
    table.add_column("Status")

    for entry in entries[:limit]:
        status = entry.availability or ("LIVE" if entry.is_live else "OK")
        table.add_row(
            str(entry.index),
            (entry.title or "Unknown")[:60],
            entry.uploader or "-",
            format_duration(entry.duration),
            status,
        )
    if len(entries) > limit:
        table.add_row("...", f"({len(entries) - limit} more)", "", "", "")
    return table


def history_table(records: list[HistoryRecord]) -> Table:
    """Build a table listing download history records."""
    table = Table(title="Download History")
    table.add_column("Date", style="muted")
    table.add_column("Title")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Size")

    for r in records:
        status_style = {
            "success": "success",
            "failed": "error",
            "skipped": "warning",
        }.get(r.status, "")
        table.add_row(
            r.date,
            r.title[:50],
            r.type,
            f"[{status_style}]{r.status}[/{status_style}]" if status_style else r.status,
            format_filesize(r.file_size),
        )
    return table


def search_results_table(results: list[VideoInfo]) -> Table:
    """Build a table listing YouTube search results."""
    table = Table(title="Search Results")
    table.add_column("#", style="menu.number", justify="right")
    table.add_column("Title")
    table.add_column("Channel")
    table.add_column("Duration")
    table.add_column("Views")

    for i, v in enumerate(results, start=1):
        table.add_row(
            str(i),
            v.title[:60],
            v.uploader or "-",
            format_duration(v.duration),
            f"{v.view_count:,}" if v.view_count else "-",
        )
    return table
