"""Centralized constants used across the application."""

from __future__ import annotations

from pathlib import Path

APP_NAME = "YouTube Downloader CLI"
APP_SLUG = "ytdownloader"

# Base directory for all persistent app data (config, history, logs).
APP_DIR = Path.home() / f".{APP_SLUG}"
CONFIG_PATH = APP_DIR / "config.json"
HISTORY_PATH = APP_DIR / "history.json"
ARCHIVE_PATH = APP_DIR / "download_archive.txt"
LOG_DIR = APP_DIR / "logs"

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "ytdownloader"

VIDEO_RESOLUTIONS = ["best", "2160p", "1440p", "1080p", "720p", "480p", "360p"]
AUDIO_BITRATES = ["best", "320", "256", "192", "128"]

RESOLUTION_HEIGHTS = {
    "2160p": 2160,
    "1440p": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
}

DEFAULT_FILENAME_TEMPLATE = "%(title)s.%(ext)s"
PLAYLIST_FILENAME_TEMPLATE = "%(playlist_index)02d - %(title)s.%(ext)s"

SUPPORTED_SUBTITLE_FORMATS = ["srt", "vtt"]

HISTORY_STATUS_SUCCESS = "success"
HISTORY_STATUS_FAILED = "failed"
HISTORY_STATUS_SKIPPED = "skipped"

DOWNLOAD_TYPE_VIDEO = "video"
DOWNLOAD_TYPE_AUDIO = "audio"
DOWNLOAD_TYPE_PLAYLIST_VIDEO = "playlist_video"
DOWNLOAD_TYPE_PLAYLIST_AUDIO = "playlist_audio"
DOWNLOAD_TYPE_SUBTITLE = "subtitle"
DOWNLOAD_TYPE_THUMBNAIL = "thumbnail"

THEMES = ["dark", "light"]

MIN_FREE_DISK_SPACE_MB = 200
