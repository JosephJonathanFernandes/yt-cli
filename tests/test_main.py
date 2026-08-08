"""Tests for the application entry point's UTF-8 output safeguard."""

from __future__ import annotations

import io

from ytdownloader.main import _ensure_utf8_output


def test_ensure_utf8_output_reconfigures_streams_when_possible(mocker):
    fake_stdout = mocker.MagicMock()
    fake_stderr = mocker.MagicMock()
    mocker.patch("ytdownloader.main.sys.stdout", fake_stdout)
    mocker.patch("ytdownloader.main.sys.stderr", fake_stderr)

    _ensure_utf8_output()

    fake_stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
    fake_stderr.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")


def test_ensure_utf8_output_ignores_streams_without_reconfigure(mocker):
    """A stream lacking reconfigure() (e.g. some test/CI runners) must not crash the app."""
    plain_stream = io.StringIO()
    mocker.patch("ytdownloader.main.sys.stdout", plain_stream)
    mocker.patch("ytdownloader.main.sys.stderr", plain_stream)

    _ensure_utf8_output()  # should not raise


def test_ensure_utf8_output_swallows_reconfigure_errors(mocker):
    fake_stdout = mocker.MagicMock()
    fake_stdout.reconfigure.side_effect = ValueError("already detached")
    mocker.patch("ytdownloader.main.sys.stdout", fake_stdout)
    mocker.patch("ytdownloader.main.sys.stderr", io.StringIO())

    _ensure_utf8_output()  # should not raise
