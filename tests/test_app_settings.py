"""Tests for App settings editing helpers (value display/coercion round-trip)."""

from __future__ import annotations

from ytdownloader.app import App


def test_display_value_for_list_is_comma_joined_not_repr():
    result = App._display_value(["en", "es"], list[str])
    assert result == "en,es"


def test_display_value_for_none_is_empty_string():
    assert App._display_value(None, str) == ""


def test_display_value_for_scalar():
    assert App._display_value(5, int) == "5"


def test_coerce_value_list_field_roundtrips_from_display():
    display = App._display_value(["en"], list[str])
    assert App._coerce_value(list[str], display) == ["en"]


def test_coerce_value_list_field_multiple():
    assert App._coerce_value(list[str], "en,es,fr") == ["en", "es", "fr"]


def test_coerce_value_bool():
    assert App._coerce_value(bool, "true") is True
    assert App._coerce_value(bool, "no") is False


def test_coerce_value_int():
    assert App._coerce_value(int, "42") == 42


def test_coerce_value_float():
    assert App._coerce_value(float, "1.5") == 1.5


def test_coerce_value_none_keyword():
    assert App._coerce_value(str, "none") is None
    assert App._coerce_value(str, "") is None


def test_coerce_value_plain_string():
    assert App._coerce_value(str, "hello") == "hello"
