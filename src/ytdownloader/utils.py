"""General-purpose utility helpers used throughout the application."""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
from pathlib import Path

INVALID_FILENAME_CHARS = r'[<>:"/\\|?*\x00-\x1f]'


def sanitize_filename(name: str, max_length: int = 200) -> str:
    """Remove characters that are invalid in filenames on major platforms."""
    cleaned = re.sub(INVALID_FILENAME_CHARS, "_", name).strip()
    cleaned = cleaned.rstrip(". ")
    if not cleaned:
        cleaned = "untitled"
    return cleaned[:max_length]


def unique_path(path: Path) -> Path:
    """Return a path that does not collide with an existing file.

    Appends " (1)", " (2)", etc. to the stem until a free path is found.
    """
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def is_ffmpeg_available() -> bool:
    """Check whether FFmpeg is available on the system PATH."""
    return shutil.which("ffmpeg") is not None


def get_ffmpeg_path() -> str | None:
    """Return the resolved path to the FFmpeg executable, if any."""
    return shutil.which("ffmpeg")


_VLC_WINDOWS_CANDIDATES = (
    Path("C:/Program Files/VideoLAN/VLC/vlc.exe"),
    Path("C:/Program Files (x86)/VideoLAN/VLC/vlc.exe"),
)


def get_vlc_path() -> str | None:
    """Return the resolved path to the VLC executable, if any.

    Checks the system PATH first (covers Linux/macOS and Windows installs
    that were added to PATH), then falls back to the default Windows
    install locations, since the official Windows installer does not
    always add VLC to PATH.
    """
    on_path = shutil.which("vlc")
    if on_path:
        return on_path
    if get_platform_name() == "windows":
        for candidate in _VLC_WINDOWS_CANDIDATES:
            if candidate.exists():
                return str(candidate)
    return None


def is_vlc_available() -> bool:
    """Check whether a VLC executable can be located."""
    return get_vlc_path() is not None


def format_duration(seconds: float | None) -> str:
    """Format a duration in seconds as ``H:MM:SS`` or ``M:SS``."""
    if seconds is None:
        return "Unknown"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_filesize(num_bytes: float | None) -> str:
    """Format a byte count as a human-readable size string."""
    if num_bytes is None:
        return "Unknown"
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_upload_date(date_str: str | None) -> str:
    """Format a yt-dlp ``YYYYMMDD`` date string as ``YYYY-MM-DD``."""
    if not date_str or len(date_str) != 8:
        return "Unknown"
    return f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"


def get_free_disk_space_mb(path: Path) -> float:
    """Return free disk space in megabytes for the filesystem containing ``path``."""
    path = Path(path)
    while not path.exists():
        if path.parent == path:
            break
        path = path.parent
    usage = shutil.disk_usage(path)
    return usage.free / (1024 * 1024)


def get_platform_name() -> str:
    """Return a normalized platform name: windows, linux, or darwin."""
    return platform.system().lower()


def open_file_or_folder(path: Path) -> bool:
    """Open a file or folder using the OS default handler. Returns success."""
    system = get_platform_name()
    try:
        if system == "windows":
            import os

            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
        return True
    except OSError:
        return False


def get_clipboard_text() -> str | None:
    """Return clipboard text content, or None if unavailable."""
    try:
        import pyperclip  # type: ignore

        text = pyperclip.paste()
        return text.strip() if text else None
    except Exception:
        return None
