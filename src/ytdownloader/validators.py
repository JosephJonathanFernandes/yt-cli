"""Input validation helpers for URLs, ranges, dates, and templates."""

from __future__ import annotations

import re
from datetime import datetime

_YOUTUBE_HOST_RE = re.compile(
    r"^(https?://)?(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/", re.IGNORECASE
)

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def is_valid_youtube_url(text: str) -> bool:
    """Return True if ``text`` looks like a YouTube video/playlist/channel URL."""
    if not text:
        return False
    text = text.strip()
    if _VIDEO_ID_RE.match(text):
        return True
    return bool(_YOUTUBE_HOST_RE.match(text))


def is_playlist_url(text: str) -> bool:
    """Return True if the URL appears to reference a playlist."""
    return "list=" in text or "/playlist" in text


def normalize_url(text: str) -> str:
    """Normalize a bare video ID or partial URL into a full https URL."""
    text = text.strip()
    if _VIDEO_ID_RE.match(text):
        return f"https://www.youtube.com/watch?v={text}"
    if text.startswith("www."):
        return f"https://{text}"
    if not text.startswith("http"):
        return f"https://{text}"
    return text


def parse_index_range(spec: str, total: int) -> list[int]:
    """Parse a playlist selection spec into a sorted list of 1-based indices.

    Supports: "25-60", "1,3,5", "1-3,7,10-12". Values are clamped to
    ``[1, total]`` and duplicates are removed.
    """
    if not spec:
        return list(range(1, total + 1))

    indices: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            try:
                start, end = int(start_str), int(end_str)
            except ValueError:
                raise ValueError(f"Invalid range segment: '{part}'")
            if start > end:
                start, end = end, start
            for i in range(start, end + 1):
                if 1 <= i <= total:
                    indices.add(i)
        else:
            try:
                i = int(part)
            except ValueError:
                raise ValueError(f"Invalid index: '{part}'")
            if 1 <= i <= total:
                indices.add(i)

    return sorted(indices)


def is_valid_date_str(date_str: str) -> bool:
    """Validate a ``YYYYMMDD`` date string."""
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except (ValueError, TypeError):
        return False


def is_valid_regex(pattern: str) -> bool:
    """Return True if ``pattern`` compiles as a valid regex."""
    try:
        re.compile(pattern)
        return True
    except re.error:
        return False


def is_valid_filename_template(template: str) -> bool:
    """Basic sanity check that a yt-dlp output template contains a field."""
    return bool(re.search(r"%\([a-zA-Z_]+\)s|%\([a-zA-Z_]+\)\d*d", template))


_EMBEDDED_URL_RE = re.compile(
    r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)/[^\s\"'<>]+",
    re.IGNORECASE,
)
_TRAILING_PUNCTUATION = ".,;:!?)]}\"'"


def extract_youtube_urls(text: str) -> list[str]:
    """Find and normalize every YouTube URL embedded anywhere in ``text``.

    Unlike :func:`is_valid_youtube_url`, this does not require the entire
    string to be a URL. It is designed for free-form content such as CSV
    cells, spreadsheet exports, or notes files where a link is mixed in
    with titles, dates, or other text.
    """
    if not text:
        return []
    found: list[str] = []
    for match in _EMBEDDED_URL_RE.findall(text):
        candidate = match.rstrip(_TRAILING_PUNCTUATION)
        if is_valid_youtube_url(candidate):
            found.append(normalize_url(candidate))
    return found
