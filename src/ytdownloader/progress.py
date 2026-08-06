"""Rich-based progress reporting for downloads.

Wraps yt-dlp progress hooks and exposes a simple, reusable Rich progress
bar with speed, ETA, and size columns.
"""

from __future__ import annotations

from typing import Any, Callable

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ytdownloader.utils import format_filesize


def build_progress() -> Progress:
    """Build a standard Rich :class:`Progress` instance for downloads."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.fields[label]}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    )


class DownloadProgressReporter:
    """Bridges yt-dlp progress hook dicts into a Rich progress bar task."""

    def __init__(self, progress: Progress, label: str) -> None:
        self.progress = progress
        self.task_id = progress.add_task("download", label=label, total=None)
        self._label = label

    def hook(self, data: dict[str, Any]) -> None:
        """yt-dlp progress hook callback."""
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            if total:
                self.progress.update(self.task_id, total=total, completed=downloaded)
            else:
                self.progress.update(self.task_id, completed=downloaded)
        elif status == "finished":
            task = self.progress.tasks[self.task_id]
            total = task.total if task.total else data.get("total_bytes") or data.get("downloaded_bytes")
            if total:
                self.progress.update(self.task_id, total=total, completed=total)

    def set_label(self, label: str) -> None:
        """Update the visible task label (e.g. 'Video 3/10')."""
        self._label = label
        self.progress.update(self.task_id, label=label)


def make_progress_hook(reporter: DownloadProgressReporter) -> Callable[[dict[str, Any]], None]:
    """Return a plain callable suitable for yt-dlp's ``progress_hooks``."""
    return reporter.hook


def summarize_result(info: dict[str, Any]) -> str:
    """Build a short human-readable summary line for a completed download."""
    title = info.get("title", "Unknown")
    size = info.get("filesize") or info.get("filesize_approx")
    size_str = format_filesize(size) if size else ""
    return f"{title} ({size_str})" if size_str else title
