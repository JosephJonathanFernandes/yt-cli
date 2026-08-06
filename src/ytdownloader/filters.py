"""Playlist filtering logic, kept separate from download/business logic."""

from __future__ import annotations

import re

from ytdownloader.models import PlaylistEntry, PlaylistFilters

_SHORT_MAX_DURATION = 60.0


def entry_matches(entry: PlaylistEntry, filters: PlaylistFilters) -> bool:
    """Return True if ``entry`` passes all configured ``filters``."""
    duration = entry.duration

    if filters.skip_unavailable and entry.availability in ("private", "removed", "unavailable"):
        return False
    if filters.skip_private and entry.availability == "private":
        return False
    if filters.skip_live and entry.is_live:
        return False
    if filters.skip_premieres and entry.is_premiere:
        return False
    if filters.skip_shorts and duration is not None and duration <= _SHORT_MAX_DURATION:
        return False

    if filters.min_duration is not None and (duration is None or duration < filters.min_duration):
        return False
    if filters.max_duration is not None and (duration is None or duration > filters.max_duration):
        return False

    if filters.uploaded_after is not None:
        if not entry.upload_date or entry.upload_date < filters.uploaded_after:
            return False
    if filters.uploaded_before is not None:
        if not entry.upload_date or entry.upload_date > filters.uploaded_before:
            return False

    title = entry.title or ""
    if filters.include_keywords and not any(
        kw.lower() in title.lower() for kw in filters.include_keywords
    ):
        return False
    if filters.exclude_keywords and any(
        kw.lower() in title.lower() for kw in filters.exclude_keywords
    ):
        return False
    if filters.title_regex:
        try:
            if not re.search(filters.title_regex, title, re.IGNORECASE):
                return False
        except re.error:
            pass

    if filters.channel_filter and entry.uploader:
        if filters.channel_filter.lower() not in entry.uploader.lower():
            return False

    if filters.url_whitelist and entry.url:
        if not any(w in entry.url for w in filters.url_whitelist):
            return False
    if filters.url_blacklist and entry.url:
        if any(b in entry.url for b in filters.url_blacklist):
            return False

    return True


def apply_filters(
    entries: list[PlaylistEntry], filters: PlaylistFilters
) -> list[PlaylistEntry]:
    """Return the subset of ``entries`` that pass ``filters``."""
    return [e for e in entries if entry_matches(e, filters)]


def select_by_range(entries: list[PlaylistEntry], indices: list[int]) -> list[PlaylistEntry]:
    """Select entries whose 1-based playlist index is in ``indices``."""
    index_set = set(indices)
    return [e for e in entries if e.index in index_set]


def select_first_n(entries: list[PlaylistEntry], n: int) -> list[PlaylistEntry]:
    """Return the first ``n`` entries."""
    return entries[:n]


def select_last_n(entries: list[PlaylistEntry], n: int) -> list[PlaylistEntry]:
    """Return the last ``n`` entries."""
    return entries[-n:] if n > 0 else []
