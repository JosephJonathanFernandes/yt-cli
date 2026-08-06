"""Pydantic data models shared across the application."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from ytdownloader.constants import (
    ARCHIVE_PATH,
    DEFAULT_FILENAME_TEMPLATE,
    DEFAULT_OUTPUT_DIR,
)


class Settings(BaseModel):
    """Persistent, user-editable application settings."""

    output_dir: str = Field(default=str(DEFAULT_OUTPUT_DIR))
    default_video_quality: str = Field(default="best")
    default_audio_quality: str = Field(default="best")
    concurrent_downloads: int = Field(default=1, ge=1, le=10)
    retry_attempts: int = Field(default=3, ge=0, le=20)
    theme: str = Field(default="dark")
    overwrite_existing: bool = Field(default=False)
    skip_existing: bool = Field(default=True)
    auto_update_ytdlp: bool = Field(default=False)
    embed_thumbnail: bool = Field(default=True)
    embed_metadata: bool = Field(default=True)
    filename_template: str = Field(default=DEFAULT_FILENAME_TEMPLATE)
    cookie_file: Optional[str] = Field(default=None)
    proxy: Optional[str] = Field(default=None)
    rate_limit: Optional[str] = Field(default=None)  # e.g. "1M" for 1MB/s
    sleep_interval: float = Field(default=0.0, ge=0.0)
    random_delay: bool = Field(default=False)
    resume_downloads: bool = Field(default=True)
    download_archive_path: str = Field(default=str(ARCHIVE_PATH))
    subtitle_languages: list[str] = Field(default_factory=lambda: ["en"])
    download_auto_subs: bool = Field(default=False)

    model_config = ConfigDict(extra="ignore")


class HistoryRecord(BaseModel):
    """A single entry in the download history."""

    id: str
    title: str
    url: str
    date: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    type: str
    resolution_or_bitrate: Optional[str] = None
    duration: Optional[float] = None
    output_path: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    error_message: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    playlist_name: Optional[str] = None


class FormatInfo(BaseModel):
    """A single downloadable format for a video."""

    format_id: str
    ext: str
    resolution: Optional[str] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    filesize: Optional[int] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    abr: Optional[float] = None


class VideoInfo(BaseModel):
    """Metadata for a single video, extracted before downloading."""

    id: str
    title: str
    url: str
    uploader: Optional[str] = None
    duration: Optional[float] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    formats: list[FormatInfo] = Field(default_factory=list)
    is_live: bool = False
    is_upcoming: bool = False
    age_limit: int = 0
    availability: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)


class PlaylistEntry(BaseModel):
    """A lightweight entry representing one item in a playlist."""

    index: int
    id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    duration: Optional[float] = None
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    is_live: bool = False
    is_premiere: bool = False
    availability: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)


class PlaylistInfo(BaseModel):
    """Metadata for a playlist, extracted before downloading."""

    id: str
    title: str
    url: str
    uploader: Optional[str] = None
    entries: list[PlaylistEntry] = Field(default_factory=list)

    @property
    def total_videos(self) -> int:
        return len(self.entries)

    @property
    def total_duration(self) -> float:
        return sum(e.duration or 0.0 for e in self.entries)

    @property
    def unavailable_count(self) -> int:
        return sum(1 for e in self.entries if e.availability not in (None, "public", "unlisted"))


class PlaylistFilters(BaseModel):
    """Advanced filtering options applied to playlist entries."""

    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    skip_shorts: bool = False
    skip_live: bool = False
    skip_premieres: bool = False
    skip_unavailable: bool = True
    skip_private: bool = True
    uploaded_after: Optional[str] = None  # YYYYMMDD
    uploaded_before: Optional[str] = None  # YYYYMMDD
    include_keywords: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    title_regex: Optional[str] = None
    channel_filter: Optional[str] = None
    url_whitelist: list[str] = Field(default_factory=list)
    url_blacklist: list[str] = Field(default_factory=list)


class DownloadResult(BaseModel):
    """Outcome of a single download operation."""

    success: bool
    title: str = ""
    url: str = ""
    output_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    skipped: bool = False
