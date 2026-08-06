"""Tests for playlist filtering logic."""

from __future__ import annotations

from ytdownloader.filters import apply_filters, select_first_n, select_last_n
from ytdownloader.models import PlaylistEntry, PlaylistFilters


def make_entry(**kwargs) -> PlaylistEntry:
    defaults = dict(index=1, id="abc", title="Video", url="https://youtu.be/abc", duration=300)
    defaults.update(kwargs)
    return PlaylistEntry(**defaults)


def test_min_duration_filter():
    entries = [make_entry(index=1, duration=100), make_entry(index=2, duration=700)]
    filters = PlaylistFilters(min_duration=600)
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [2]


def test_max_duration_filter():
    entries = [make_entry(index=1, duration=100), make_entry(index=2, duration=700)]
    filters = PlaylistFilters(max_duration=200)
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [1]


def test_skip_shorts():
    entries = [make_entry(index=1, duration=30), make_entry(index=2, duration=300)]
    filters = PlaylistFilters(skip_shorts=True)
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [2]


def test_skip_live():
    entries = [make_entry(index=1, is_live=True), make_entry(index=2, is_live=False)]
    filters = PlaylistFilters(skip_live=True)
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [2]


def test_include_keywords():
    entries = [make_entry(index=1, title="Python Tutorial"), make_entry(index=2, title="Vlog")]
    filters = PlaylistFilters(include_keywords=["tutorial"])
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [1]


def test_exclude_keywords():
    entries = [make_entry(index=1, title="Movie Trailer"), make_entry(index=2, title="Full Movie")]
    filters = PlaylistFilters(exclude_keywords=["trailer"])
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [2]


def test_title_regex():
    entries = [make_entry(index=1, title="01 - Intro"), make_entry(index=2, title="Extra")]
    filters = PlaylistFilters(title_regex=r"^\d+ - ")
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [1]


def test_uploaded_after_before():
    entries = [
        make_entry(index=1, upload_date="20230101"),
        make_entry(index=2, upload_date="20240601"),
    ]
    filters = PlaylistFilters(uploaded_after="20240101")
    assert [e.index for e in apply_filters(entries, filters)] == [2]

    filters2 = PlaylistFilters(uploaded_before="20230601")
    assert [e.index for e in apply_filters(entries, filters2)] == [1]


def test_skip_unavailable_default_true():
    entries = [
        make_entry(index=1, availability="public"),
        make_entry(index=2, availability="private"),
    ]
    filters = PlaylistFilters()
    result = apply_filters(entries, filters)
    assert [e.index for e in result] == [1]


def test_select_first_n_and_last_n():
    entries = [make_entry(index=i) for i in range(1, 11)]
    assert [e.index for e in select_first_n(entries, 3)] == [1, 2, 3]
    assert [e.index for e in select_last_n(entries, 3)] == [8, 9, 10]
