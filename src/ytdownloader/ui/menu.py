"""Main menu rendering for the interactive CLI."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from ytdownloader.constants import APP_NAME

MAIN_MENU_ITEMS = [
    ("1", "Download Single Video"),
    ("2", "Download Playlist"),
    ("3", "Download Audio (MP3)"),
    ("4", "Download Playlist as MP3"),
    ("5", "Download Subtitles"),
    ("6", "Download Thumbnail"),
    ("7", "Batch Download from File"),
    ("8", "Search YouTube"),
    ("9", "Watch in VLC"),
    ("10", "Settings"),
    ("11", "View Download History"),
    ("12", "Help"),
    ("13", "Exit"),
]


def render_main_menu(console: Console) -> None:
    """Render the polished main menu panel."""
    lines = [f"[menu.number]{num:>2}.[/menu.number] [menu.text]{label}[/menu.text]" for num, label in MAIN_MENU_ITEMS]
    body = "\n".join(lines)
    panel = Panel(
        body,
        title=f"[title]{APP_NAME}[/title]",
        subtitle="[subtitle]Select an option[/subtitle]",
        border_style="highlight",
        padding=(1, 2),
    )
    console.print(panel)


def render_header(console: Console, title: str) -> None:
    """Render a consistent sub-screen header panel."""
    console.print(Panel(f"[title]{title}[/title]", border_style="highlight"))
