"""Reusable interactive prompt helpers with consistent navigation support.

Every prompt in this module supports the navigation keywords ``back``,
``cancel``, and ``help`` where applicable, returning ``None`` (or raising
:class:`NavigationSignal`) so calling code can react uniformly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from rich.console import Console
from rich.prompt import Confirm, Prompt

NAV_BACK = "__back__"
NAV_CANCEL = "__cancel__"
NAV_HELP = "__help__"

_NAV_KEYWORDS = {
    "back": NAV_BACK,
    "b": NAV_BACK,
    "cancel": NAV_CANCEL,
    "c": NAV_CANCEL,
    "help": NAV_HELP,
    "h": NAV_HELP,
}


class NavigationSignal(Exception):
    """Raised to signal a navigation action (back/cancel) from a prompt."""

    def __init__(self, action: str) -> None:
        super().__init__(action)
        self.action = action


def check_nav(text: str) -> Optional[str]:
    """Return a navigation constant if ``text`` is a nav keyword, else None."""
    return _NAV_KEYWORDS.get(text.strip().lower())


def prompt_text(
    console: Console,
    message: str,
    default: Optional[str] = None,
    allow_empty: bool = False,
) -> Optional[str]:
    """Prompt for free text. Returns None on back/cancel navigation."""
    hint = " [muted](type 'back' to return, 'cancel' to abort)[/muted]"
    while True:
        value = Prompt.ask(f"{message}{hint}", default=default or "")
        nav = check_nav(value)
        if nav in (NAV_BACK, NAV_CANCEL):
            return None
        if nav == NAV_HELP:
            console.print("[info]Enter a value, or type 'back'/'cancel' to navigate.[/info]")
            continue
        if not value and not allow_empty:
            console.print("[warning]A value is required.[/warning]")
            continue
        return value


def prompt_choice(
    console: Console,
    message: str,
    choices: Sequence[str],
    default: Optional[str] = None,
) -> Optional[str]:
    """Prompt for a value constrained to ``choices``. Returns None on back/cancel.

    Matching is case-insensitive; the original casing from ``choices`` is
    always returned.
    """
    options_str = "/".join(choices)
    hint = f" [muted]({options_str}, or 'back'/'cancel')[/muted]"
    lookup = {c.lower(): c for c in choices}
    while True:
        raw = Prompt.ask(f"{message}{hint}", default=default)
        nav = check_nav(raw)
        if nav in (NAV_BACK, NAV_CANCEL):
            return None
        if nav == NAV_HELP:
            console.print(f"[info]Valid options: {', '.join(choices)}[/info]")
            continue
        matched = lookup.get(raw.strip().lower())
        if matched is None:
            console.print(f"[warning]Please choose one of: {options_str}[/warning]")
            continue
        return matched


def prompt_int(
    console: Console,
    message: str,
    default: Optional[int] = None,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> Optional[int]:
    """Prompt for an integer within an optional range. Returns None on back/cancel."""
    hint = " [muted](or 'back'/'cancel')[/muted]"
    while True:
        raw = Prompt.ask(f"{message}{hint}", default=str(default) if default is not None else "")
        nav = check_nav(raw)
        if nav in (NAV_BACK, NAV_CANCEL):
            return None
        if nav == NAV_HELP:
            console.print("[info]Enter a whole number.[/info]")
            continue
        try:
            value = int(raw)
        except ValueError:
            console.print("[warning]Please enter a valid whole number.[/warning]")
            continue
        if min_value is not None and value < min_value:
            console.print(f"[warning]Value must be at least {min_value}.[/warning]")
            continue
        if max_value is not None and value > max_value:
            console.print(f"[warning]Value must be at most {max_value}.[/warning]")
            continue
        return value


def prompt_confirm(console: Console, message: str, default: bool = True) -> bool:
    """Prompt for a yes/no confirmation."""
    return Confirm.ask(message, default=default)


def prompt_path(console: Console, message: str, must_exist: bool = False) -> Optional[Path]:
    """Prompt for a filesystem path. Returns None on back/cancel."""
    while True:
        raw = prompt_text(console, message)
        if raw is None:
            return None
        path = Path(raw).expanduser()
        if must_exist and not path.exists():
            console.print(f"[warning]Path does not exist: {path}[/warning]")
            continue
        return path


def prompt_url(console: Console, message: str = "Enter YouTube URL") -> Optional[str]:
    """Prompt for a URL, offering clipboard auto-detection if available."""
    from ytdownloader.utils import get_clipboard_text
    from ytdownloader.validators import is_valid_youtube_url, normalize_url

    clipboard = get_clipboard_text()
    if clipboard and is_valid_youtube_url(clipboard):
        console.print(f"[info]Detected YouTube URL in clipboard:[/info] {clipboard}")
        if prompt_confirm(console, "Use this URL?", default=True):
            return normalize_url(clipboard)

    value = prompt_text(console, message)
    if value is None:
        return None
    return normalize_url(value)
