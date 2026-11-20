"""Tests for Rich table builders."""

from __future__ import annotations

from rich.console import Console

from ytdownloader.models import FormatInfo, HistoryRecord, PlaylistEntry, VideoInfo
from ytdownloader.ui.tables import (
    formats_table,
    history_table,
    playlist_entries_table,
    search_results_table,
    video_details_table,
)


from ytdownloader.ui.theme import get_theme


def _render(renderable) -> str:
    console = Console(theme=get_theme("dark"), record=True, width=120)
    console.print(renderable)
    return console.export_text()


def test_video_details_table_shows_metadata_and_status_badges():
    info = VideoInfo(
        id="abc",
        title="Live Premiere",
        url="https://youtu.be/abc",
        uploader="Creator",
        duration=125,
        view_count=12345,
        upload_date="20250115",
        description="First line description",
        is_live=True,
        age_limit=18,
    )
    output = _render(video_details_table(info))
    assert "Live Premiere" in output
    assert "Creator" in output
    assert "12,345" in output
    assert "2025-01-15" in output
    assert "LIVE" in output
    assert "Age 18+" in output


def test_formats_table_renders_format_rows():
    fmt = FormatInfo(
        format_id="137",
        ext="mp4",
        resolution="1920x1080",
        height=1080,
        fps=60.0,
        filesize=1048576,
        vcodec="avc1",
        acodec="none",
    )
    output = _render(formats_table([fmt]))
    assert "137" in output
    assert "1920x1080" in output
    assert "1.0 MB" in output


def test_playlist_entries_table_truncates_beyond_limit():
    entries = [PlaylistEntry(index=i, title=f"Track {i}") for i in range(1, 6)]
    output = _render(playlist_entries_table(entries, limit=3))
    assert "Track 1" in output
    assert "Track 3" in output
    assert "(2 more)" in output


def test_history_and_search_tables_render_rows():
    record = HistoryRecord(
        id="1",
        title="Saved Clip",
        url="https://youtu.be/abc",
        type="video",
        status="success",
        file_size=2048,
    )
    assert "Saved Clip" in _render(history_table([record]))

    video = VideoInfo(id="abc", title="Found Clip", url="https://youtu.be/abc", view_count=500)
    assert "Found Clip" in _render(search_results_table([video]))
