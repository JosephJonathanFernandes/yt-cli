"""Custom exception hierarchy for predictable, user-friendly error handling."""

from __future__ import annotations


class YTDownloaderError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class InvalidURLError(YTDownloaderError):
    """Raised when a provided URL is not a valid/supported URL."""


class VideoUnavailableError(YTDownloaderError):
    """Raised when a video is private, deleted, or otherwise unavailable."""


class AgeRestrictedError(YTDownloaderError):
    """Raised when a video is age restricted and cannot be accessed."""


class PlaylistUnavailableError(YTDownloaderError):
    """Raised when a playlist cannot be resolved or accessed."""


class NetworkError(YTDownloaderError):
    """Raised for connectivity issues, timeouts, or DNS failures."""


class FFmpegNotFoundError(YTDownloaderError):
    """Raised when FFmpeg is required but not found on the system."""


class VLCNotFoundError(YTDownloaderError):
    """Raised when VLC is required (for streaming playback) but not found."""


class DiskSpaceError(YTDownloaderError):
    """Raised when there is insufficient disk space for a download."""


class PermissionDeniedError(YTDownloaderError):
    """Raised when the app lacks permission to write files."""


class AuthenticationError(YTDownloaderError):
    """Raised when authentication (cookies/login) fails."""


class RateLimitError(YTDownloaderError):
    """Raised when the remote service throttles or rate limits requests."""


class ConfigError(YTDownloaderError):
    """Raised for configuration load/save/validation issues."""


class DownloadError(YTDownloaderError):
    """Generic download failure wrapper for unexpected yt-dlp errors."""


class AlreadyDownloadedError(YTDownloaderError):
    """Raised when yt-dlp skips an item because it is already in the download archive.

    This is not a failure; callers should treat it as a successful no-op.
    """
