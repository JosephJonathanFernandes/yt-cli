"""Tests for URL validation, normalization, and range parsing."""

from __future__ import annotations

import pytest

from ytdownloader.validators import (
    extract_youtube_urls,
    is_playlist_url,
    is_valid_date_str,
    is_valid_filename_template,
    is_valid_regex,
    is_valid_youtube_url,
    normalize_url,
    parse_index_range,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "http://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "youtube.com/watch?v=dQw4w9WgXcQ",
        "dQw4w9WgXcQ",
    ],
)
def test_is_valid_youtube_url_true(url):
    assert is_valid_youtube_url(url) is True


@pytest.mark.parametrize("url", ["", "not a url", "https://vimeo.com/12345", "http://example.com"])
def test_is_valid_youtube_url_false(url):
    assert is_valid_youtube_url(url) is False


def test_is_playlist_url():
    assert is_playlist_url("https://www.youtube.com/playlist?list=PL123")
    assert is_playlist_url("https://www.youtube.com/watch?v=abc&list=PL123")
    assert not is_playlist_url("https://www.youtube.com/watch?v=abc")


def test_normalize_url_bare_id():
    assert normalize_url("dQw4w9WgXcQ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_normalize_url_adds_scheme():
    assert normalize_url("www.youtube.com/watch?v=abc").startswith("https://")


def test_normalize_url_keeps_full_url():
    url = "https://www.youtube.com/watch?v=abc"
    assert normalize_url(url) == url


def test_parse_index_range_simple_range():
    assert parse_index_range("2-5", 10) == [2, 3, 4, 5]


def test_parse_index_range_commas():
    assert parse_index_range("1,3,5", 10) == [1, 3, 5]


def test_parse_index_range_mixed():
    assert parse_index_range("1-3,7,10-12", 20) == [1, 2, 3, 7, 10, 11, 12]


def test_parse_index_range_clamps_to_total():
    assert parse_index_range("5-50", 10) == [5, 6, 7, 8, 9, 10]


def test_parse_index_range_empty_returns_all():
    assert parse_index_range("", 3) == [1, 2, 3]


def test_parse_index_range_invalid_raises():
    with pytest.raises(ValueError):
        parse_index_range("abc", 10)


def test_is_valid_date_str():
    assert is_valid_date_str("20240115") is True
    assert is_valid_date_str("2024-01-15") is False
    assert is_valid_date_str("bad") is False


def test_is_valid_regex():
    assert is_valid_regex(r"^Tutorial.*$") is True
    assert is_valid_regex(r"(unclosed") is False


def test_is_valid_filename_template():
    assert is_valid_filename_template("%(title)s.%(ext)s") is True
    assert is_valid_filename_template("no_placeholders") is False


def test_extract_youtube_urls_from_plain_url():
    assert extract_youtube_urls("https://www.youtube.com/watch?v=wbFXZhq8bnw") == [
        "https://www.youtube.com/watch?v=wbFXZhq8bnw"
    ]


def test_extract_youtube_urls_embedded_in_title_with_emoji():
    text = "Abstract Posters - Beat Shake | Music Visualization\U0001f5a4\U0001f3b6\U0001f48e https://www.youtube.com/watch?v=wbFXZhq8bnw"
    assert extract_youtube_urls(text) == ["https://www.youtube.com/watch?v=wbFXZhq8bnw"]


def test_extract_youtube_urls_strips_trailing_punctuation():
    text = "check this out (https://youtu.be/dQw4w9WgXcQ)."
    assert extract_youtube_urls(text) == ["https://youtu.be/dQw4w9WgXcQ"]


def test_extract_youtube_urls_no_link_returns_empty():
    assert extract_youtube_urls("just a regular title with no link") == []


def test_extract_youtube_urls_multiple_in_one_string():
    text = "https://youtu.be/dQw4w9WgXcQ and also https://www.youtube.com/watch?v=abcdefghijk"
    result = extract_youtube_urls(text)
    assert result == [
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=abcdefghijk",
    ]


def test_extract_youtube_urls_empty_string():
    assert extract_youtube_urls("") == []
