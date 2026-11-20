"""Tests for playlist, subtitle, and thumbnail download orchestration."""

from __future__ import annotations

from pathlib import Path

from ytdownloader.constants import PLAYLIST_FILENAME_TEMPLATE
from ytdownloader.models import DownloadResult, PlaylistEntry, Settings, VideoInfo
from ytdownloader.playlist import download_playlist_entries, entry_to_video_info
from ytdownloader.subtitles import download_subtitles
from ytdownloader.thumbnails import download_thumbnail


def test_entry_to_video_info_converts_fields():
    entry = PlaylistEntry(
        index=1,
        id="abc123",
        title="Episode 1",
        url="https://youtu.be/abc123",
        uploader="Channel",
        duration=120.0,
    )
    info = entry_to_video_info(entry)
    assert info.id == "abc123"
    assert info.title == "Episode 1"
    assert info.url == "https://youtu.be/abc123"
    assert info.uploader == "Channel"


def test_download_playlist_entries_handles_missing_url_and_uses_playlist_template(
    tmp_settings: Settings, tmp_path: Path, mocker
):
    mock_video = mocker.patch(
        "ytdownloader.playlist.download_video",
        return_value=DownloadResult(success=True, title="Valid", url="https://youtu.be/abc"),
    )
    entries = [
        PlaylistEntry(index=1, id="abc", title="Valid", url="https://youtu.be/abc"),
        PlaylistEntry(index=2, id="missing", title="No URL", url=None),
    ]

    results = download_playlist_entries(
        tmp_settings, entries, mode="mp4", resolution="720p", output_dir=tmp_path
    )

    assert len(results) == 2
    assert results[0].success is True
    assert results[1].success is False
    assert results[1].error_message == "Missing URL"
    assert mock_video.call_args.args[4] == PLAYLIST_FILENAME_TEMPLATE


def test_download_subtitles_returns_subtitle_path(
    tmp_settings: Settings, tmp_path: Path, mocker
):
    mocker.patch(
        "ytdownloader.subtitles.YTDLPWrapper.download",
        return_value={"requested_subtitles": {"en": {"filepath": str(tmp_path / "video.en.vtt")}}},
    )
    info = VideoInfo(id="abc", title="Sub Video", url="https://youtu.be/abc")
    result = download_subtitles(tmp_settings, info, languages=["en"], output_dir=tmp_path)
    assert result.success is True
    assert result.output_path == str(tmp_path / "video.en.vtt")


def test_download_thumbnail_returns_thumbnail_path(
    tmp_settings: Settings, tmp_path: Path, mocker
):
    mocker.patch(
        "ytdownloader.thumbnails.YTDLPWrapper.download",
        return_value={"thumbnails": [{"filepath": str(tmp_path / "thumb.webp")}]},
    )
    info = VideoInfo(id="abc", title="Thumb Video", url="https://youtu.be/abc")
    result = download_thumbnail(tmp_settings, info, output_dir=tmp_path)
    assert result.success is True
    assert result.output_path == str(tmp_path / "thumb.webp")
