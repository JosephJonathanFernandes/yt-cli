"""Color theme definitions for the Rich-based terminal UI."""

from __future__ import annotations

from rich.theme import Theme

DARK_THEME = Theme(
    {
        "title": "bold cyan",
        "subtitle": "dim cyan",
        "menu.number": "bold yellow",
        "menu.text": "white",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "info": "bold blue",
        "muted": "grey62",
        "highlight": "bold magenta",
    }
)

LIGHT_THEME = Theme(
    {
        "title": "bold blue",
        "subtitle": "dim blue",
        "menu.number": "bold dark_orange",
        "menu.text": "black",
        "success": "bold green",
        "warning": "bold dark_orange",
        "error": "bold red",
        "info": "bold blue",
        "muted": "grey37",
        "highlight": "bold magenta",
    }
)


def get_theme(name: str) -> Theme:
    """Return the Rich :class:`Theme` matching ``name`` ('dark' or 'light')."""
    return LIGHT_THEME if name == "light" else DARK_THEME
