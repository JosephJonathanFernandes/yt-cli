"""Tests for stream-and-play (VLC) support."""

from __future__ import annotations

import pytest

from ytdownloader.exceptions import VLCNotFoundError
from ytdownloader.stream import play_in_vlc


def test_play_in_vlc_raises_when_vlc_not_found(mocker):
    mocker.patch("ytdownloader.stream.get_vlc_path", return_value=None)
    with pytest.raises(VLCNotFoundError):
        play_in_vlc("https://example.com/stream.mp4", "Some Title")


def test_play_in_vlc_launches_subprocess_with_expected_args(mocker):
    mocker.patch("ytdownloader.stream.get_vlc_path", return_value="C:/VLC/vlc.exe")
    mock_popen = mocker.patch("ytdownloader.stream.subprocess.Popen")

    play_in_vlc("https://example.com/stream.mp4", "My Video")

    args, kwargs = mock_popen.call_args
    command = args[0]
    assert command[0] == "C:/VLC/vlc.exe"
    assert "https://example.com/stream.mp4" in command
    assert "--play-and-exit" in command
    assert "--meta-title" in command
    assert "My Video" in command


def test_play_in_vlc_without_title_omits_meta_title_flag(mocker):
    mocker.patch("ytdownloader.stream.get_vlc_path", return_value="C:/VLC/vlc.exe")
    mock_popen = mocker.patch("ytdownloader.stream.subprocess.Popen")

    play_in_vlc("https://example.com/stream.mp4")

    args, _ = mock_popen.call_args
    command = args[0]
    assert "--meta-title" not in command
