"""Tests for filename sanitization, formatting, and misc utilities."""

from __future__ import annotations

from pathlib import Path

from ytdownloader.utils import (
    format_duration,
    format_filesize,
    format_upload_date,
    sanitize_filename,
    unique_path,
)


def test_sanitize_filename_removes_invalid_chars():
    assert sanitize_filename('Video: "Best" <Ever>?') == "Video_ _Best_ _Ever__"


def test_sanitize_filename_strips_trailing_dots_and_spaces():
    assert sanitize_filename("My File.   ") == "My File"


def test_sanitize_filename_empty_becomes_untitled():
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename("   ") == "untitled"


def test_sanitize_filename_truncates_long_names():
    long_name = "a" * 300
    result = sanitize_filename(long_name, max_length=50)
    assert len(result) == 50


def test_unique_path_returns_same_path_if_free(tmp_path: Path):
    target = tmp_path / "video.mp4"
    assert unique_path(target) == target


def test_unique_path_increments_on_collision(tmp_path: Path):
    target = tmp_path / "video.mp4"
    target.write_text("x")
    result = unique_path(target)
    assert result == tmp_path / "video (1).mp4"

    result.write_text("x")
    result2 = unique_path(target)
    assert result2 == tmp_path / "video (2).mp4"


def test_format_duration_hours():
    assert format_duration(3725) == "1:02:05"


def test_format_duration_minutes_only():
    assert format_duration(125) == "2:05"


def test_format_duration_none():
    assert format_duration(None) == "Unknown"


def test_format_filesize_bytes_and_units():
    assert format_filesize(500) == "500 B"
    assert format_filesize(1536) == "1.5 KB"
    assert format_filesize(None) == "Unknown"


def test_format_upload_date():
    assert format_upload_date("20240115") == "2024-01-15"
    assert format_upload_date(None) == "Unknown"
    assert format_upload_date("bad") == "Unknown"


def test_get_vlc_path_prefers_system_path(mocker):
    from ytdownloader.utils import get_vlc_path

    mocker.patch("shutil.which", return_value="/usr/bin/vlc")
    assert get_vlc_path() == "/usr/bin/vlc"


def test_get_vlc_path_returns_none_when_not_found(mocker):
    from ytdownloader.utils import get_vlc_path

    mocker.patch("shutil.which", return_value=None)
    mocker.patch("ytdownloader.utils.get_platform_name", return_value="linux")
    assert get_vlc_path() is None


def test_get_vlc_path_falls_back_to_windows_default_location(mocker, tmp_path):
    from ytdownloader.utils import get_vlc_path

    fake_vlc = tmp_path / "vlc.exe"
    fake_vlc.write_text("")
    mocker.patch("shutil.which", return_value=None)
    mocker.patch("ytdownloader.utils.get_platform_name", return_value="windows")
    mocker.patch("ytdownloader.utils._VLC_WINDOWS_CANDIDATES", (fake_vlc,))
    assert get_vlc_path() == str(fake_vlc)


def test_is_vlc_available_true_when_path_found(mocker):
    from ytdownloader.utils import is_vlc_available

    mocker.patch("ytdownloader.utils.get_vlc_path", return_value="/usr/bin/vlc")
    assert is_vlc_available() is True


def test_is_vlc_available_false_when_not_found(mocker):
    from ytdownloader.utils import is_vlc_available

    mocker.patch("ytdownloader.utils.get_vlc_path", return_value=None)
    assert is_vlc_available() is False
