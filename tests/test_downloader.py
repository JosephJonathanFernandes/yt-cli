"""Tests for the YTDLPWrapper option building and error translation."""

from __future__ import annotations

from pathlib import Path

import pytest

from ytdownloader.downloader import YTDLPWrapper, _translate_exception
from ytdownloader.exceptions import (
    AgeRestrictedError,
    AuthenticationError,
    DownloadError,
    NetworkError,
    RateLimitError,
    VideoUnavailableError,
)
from ytdownloader.models import Settings


def test_download_video_returns_skipped_result_on_already_downloaded(
    tmp_settings: Settings, tmp_path: Path, mocker
):
    from ytdownloader.models import VideoInfo
    from ytdownloader.video import download_video

    mocker.patch(
        "ytdownloader.video.YTDLPWrapper.download",
        side_effect=__import__("ytdownloader.exceptions", fromlist=["AlreadyDownloadedError"]).AlreadyDownloadedError(
            "Already downloaded"
        ),
    )
    info = VideoInfo(id="abc", title="My Video", url="https://youtu.be/abc")
    result = download_video(tmp_settings, info, "best", tmp_path)
    assert result.success is True
    assert result.skipped is True


def test_video_format_selector_best():
    assert YTDLPWrapper._video_format_selector("best") == "bestvideo+bestaudio/best"


def test_video_format_selector_resolution():
    selector = YTDLPWrapper._video_format_selector("1080p")
    assert "height<=1080" in selector


def test_video_format_selector_unknown_falls_back_to_best():
    assert YTDLPWrapper._video_format_selector("weird") == "bestvideo+bestaudio/best"


def test_parse_rate_limit_kilobytes():
    assert YTDLPWrapper._parse_rate_limit("500K") == int(500 * 1024)


def test_parse_rate_limit_megabytes():
    assert YTDLPWrapper._parse_rate_limit("2M") == int(2 * 1024 * 1024)


def test_parse_rate_limit_invalid_returns_zero():
    assert YTDLPWrapper._parse_rate_limit("garbage") == 0


def test_build_video_opts_sets_outtmpl_and_format(tmp_settings: Settings, tmp_path: Path):
    wrapper = YTDLPWrapper(tmp_settings)
    opts = wrapper.build_video_opts(tmp_path, "%(title)s.%(ext)s", "720p")
    assert opts["outtmpl"] == str(tmp_path / "%(title)s.%(ext)s")
    assert "height<=720" in opts["format"]
    assert opts["merge_output_format"] == "mp4"


def test_build_audio_opts_sets_mp3_postprocessor(tmp_settings: Settings, tmp_path: Path):
    wrapper = YTDLPWrapper(tmp_settings)
    opts = wrapper.build_audio_opts(tmp_path, "%(title)s.%(ext)s", "192")
    pp = opts["postprocessors"][0]
    assert pp["key"] == "FFmpegExtractAudio"
    assert pp["preferredcodec"] == "mp3"
    assert pp["preferredquality"] == "192"


def test_build_audio_opts_best_quality_maps_to_zero(tmp_settings: Settings, tmp_path: Path):
    wrapper = YTDLPWrapper(tmp_settings)
    opts = wrapper.build_audio_opts(tmp_path, "%(title)s.%(ext)s", "best")
    assert opts["postprocessors"][0]["preferredquality"] == "0"


def test_build_subtitle_opts(tmp_settings: Settings, tmp_path: Path):
    wrapper = YTDLPWrapper(tmp_settings)
    opts = wrapper.build_subtitle_opts(tmp_path, "%(title)s.%(ext)s", ["en", "es"])
    assert opts["writesubtitles"] is True
    assert opts["subtitleslangs"] == ["en", "es"]
    assert opts["skip_download"] is True


def test_build_thumbnail_opts(tmp_settings: Settings, tmp_path: Path):
    wrapper = YTDLPWrapper(tmp_settings)
    opts = wrapper.build_thumbnail_opts(tmp_path, "%(title)s.%(ext)s")
    assert opts["writethumbnail"] is True
    assert opts["skip_download"] is True


def test_apply_archive_respects_skip_existing(tmp_settings: Settings):
    tmp_settings.skip_existing = True
    wrapper = YTDLPWrapper(tmp_settings)
    opts: dict = {}
    wrapper._apply_archive(opts)
    assert opts["download_archive"] == tmp_settings.download_archive_path


@pytest.mark.parametrize(
    "message,expected_type",
    [
        ("ERROR: Private video. Sign in if you've been granted access", VideoUnavailableError),
        ("This video is age restricted", AgeRestrictedError),
        ("HTTP Error 429: Too Many Requests", RateLimitError),
        ("Sign in to confirm you're not a bot", AuthenticationError),
        ("A network connection error occurred", NetworkError),
    ],
)
def test_translate_exception_maps_known_errors(message, expected_type):
    result = _translate_exception(Exception(message), url="https://youtu.be/abc")
    assert isinstance(result, expected_type)


def test_resolve_stream_url_returns_direct_url_and_info(tmp_settings: Settings, mocker):
    from ytdownloader.models import VideoInfo

    mock_ydl = mocker.MagicMock()
    mock_ydl.extract_info.return_value = {
        "id": "abc123",
        "title": "Test Video",
        "url": "https://cdn.example.com/stream.mp4",
        "uploader": "Someone",
        "duration": 120,
        "formats": [],
    }
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.__exit__.return_value = False
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    wrapper = YTDLPWrapper(tmp_settings)
    stream_url, info = wrapper.resolve_stream_url("https://youtu.be/abc123", "best")

    assert stream_url == "https://cdn.example.com/stream.mp4"
    assert isinstance(info, VideoInfo)
    assert info.title == "Test Video"


def test_resolve_stream_url_raises_when_no_url_and_no_requested_formats(
    tmp_settings: Settings, mocker
):
    mock_ydl = mocker.MagicMock()
    mock_ydl.extract_info.return_value = {"id": "abc", "title": "T", "formats": []}
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.__exit__.return_value = False
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    wrapper = YTDLPWrapper(tmp_settings)
    with pytest.raises(DownloadError):
        wrapper.resolve_stream_url("https://youtu.be/abc", "best")


def test_resolve_stream_url_raises_clear_error_for_split_formats(
    tmp_settings: Settings, mocker
):
    """When only a split video+audio format is available, raise a clear
    error instead of silently returning a video-only or missing URL."""
    mock_ydl = mocker.MagicMock()
    mock_ydl.extract_info.return_value = {
        "id": "abc",
        "title": "T",
        "requested_formats": [{"url": "video.mp4"}, {"url": "audio.webm"}],
        "formats": [],
    }
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.__exit__.return_value = False
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    wrapper = YTDLPWrapper(tmp_settings)
    with pytest.raises(DownloadError):
        wrapper.resolve_stream_url("https://youtu.be/abc", "best")


def test_base_opts_disables_playlist_expansion_by_default(tmp_settings: Settings):
    """A single video URL carrying '&list=...' must not expand into a playlist."""
    wrapper = YTDLPWrapper(tmp_settings)
    opts = wrapper._base_opts()
    assert opts["noplaylist"] is True


def test_base_opts_does_not_ignore_errors_by_default(tmp_settings: Settings):
    """Single-item downloads must raise real errors instead of silently swallowing them."""
    wrapper = YTDLPWrapper(tmp_settings)
    opts = wrapper._base_opts()
    assert opts["ignoreerrors"] is False


def test_resolve_thumbnail_path_from_thumbnails_list():
    info = {
        "requested_downloads": [{"filepath": "video.webm"}],
        "thumbnails": [
            {"id": "0"},
            {"id": "38", "filepath": "thumb.webp"},
        ],
    }
    assert YTDLPWrapper.resolve_thumbnail_path(info) == "thumb.webp"


def test_resolve_thumbnail_path_missing_returns_none():
    assert YTDLPWrapper.resolve_thumbnail_path({}) is None


def test_resolve_subtitle_paths_from_requested_subtitles():
    info = {
        "requested_downloads": [{"filepath": "video.webm"}],
        "requested_subtitles": {
            "en": {"filepath": "video.en.vtt"},
        },
    }
    assert YTDLPWrapper.resolve_subtitle_paths(info) == ["video.en.vtt"]


def test_resolve_subtitle_paths_missing_returns_empty_list():
    assert YTDLPWrapper.resolve_subtitle_paths({}) == []


def test_download_raises_already_downloaded_when_archive_skips_silently(
    tmp_settings: Settings, tmp_path: Path, mocker
):
    """A None result with a download_archive configured must be treated as a
    skip (already downloaded), not a generic download failure."""
    from ytdownloader.exceptions import AlreadyDownloadedError

    wrapper = YTDLPWrapper(tmp_settings)
    opts = {"download_archive": str(tmp_path / "archive.txt")}

    mock_ydl = mocker.MagicMock()
    mock_ydl.extract_info.return_value = None
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.__exit__.return_value = False
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    with pytest.raises(AlreadyDownloadedError):
        wrapper.download("https://youtu.be/abc", opts)


def test_download_raises_generic_error_when_no_archive_and_none_result(
    tmp_settings: Settings, mocker
):
    """Without a download_archive, a None result is a genuine failure."""
    from ytdownloader.exceptions import DownloadError

    wrapper = YTDLPWrapper(tmp_settings)
    opts: dict = {}

    mock_ydl = mocker.MagicMock()
    mock_ydl.extract_info.return_value = None
    mock_ydl.__enter__.return_value = mock_ydl
    mock_ydl.__exit__.return_value = False
    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ydl)

    with pytest.raises(DownloadError):
        wrapper.download("https://youtu.be/abc", opts)
