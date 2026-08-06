"""Tests for prompt helper behavior: navigation keywords and choice matching."""

from __future__ import annotations

from ytdownloader.prompts import check_nav, NAV_BACK, NAV_CANCEL, NAV_HELP


def test_check_nav_recognizes_back_variants():
    assert check_nav("back") == NAV_BACK
    assert check_nav("Back") == NAV_BACK
    assert check_nav("b") == NAV_BACK


def test_check_nav_recognizes_cancel_variants():
    assert check_nav("cancel") == NAV_CANCEL
    assert check_nav("CANCEL") == NAV_CANCEL
    assert check_nav("c") == NAV_CANCEL


def test_check_nav_recognizes_help_variants():
    assert check_nav("help") == NAV_HELP
    assert check_nav("h") == NAV_HELP


def test_check_nav_returns_none_for_regular_input():
    assert check_nav("mp4") is None
    assert check_nav("1080p") is None
