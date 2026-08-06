"""Centralized yt-dlp wrapper.

All direct interaction with yt-dlp is confined to this module so the rest
of the application never needs to know about yt-dlp's option dictionaries
or error types.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from ytdownloader.constants import RESOLUTION_HEIGHTS
from ytdownloader.exceptions import (
    AgeRestrictedError,
    AlreadyDownloadedError,
    AuthenticationError,
    DownloadError,
    FFmpegNotFoundError,
    NetworkError,
    PlaylistUnavailableError,
    RateLimitError,
    VideoUnavailableError,
)
from ytdownloader.logger import get_logger
from ytdownloader.models import FormatInfo, PlaylistEntry, PlaylistInfo, Settings, VideoInfo
from ytdownloader.utils import is_ffmpeg_available

logger = get_logger()

ProgressHook = Callable[[dict[str, Any]], None]


def _translate_exception(exc: Exception, url: str = "") -> Exception:
    """Map a raw yt-dlp/urllib exception to a domain-specific exception."""
    message = str(exc).lower()

    if "private video" in message or "video unavailable" in message or "has been removed" in message:
        return VideoUnavailableError(f"Video unavailable: {url}", hint="The video may be private, deleted, or removed.")
    if "sign in to confirm your age" in message or "age" in message and "restrict" in message:
        return AgeRestrictedError(
            f"Age-restricted video: {url}",
            hint="Provide a cookie file in Settings to access age-restricted content.",
        )
    if "playlist does not exist" in message or "unable to download webpage" in message and "playlist" in message:
        return PlaylistUnavailableError(f"Playlist unavailable: {url}")
    if "http error 429" in message or "429" in message:
        return RateLimitError(
            "YouTube is rate-limiting requests.",
            hint="Wait a while and try again, or lower concurrent downloads.",
        )
    if "sign in" in message or "login required" in message or "cookies" in message:
        return AuthenticationError(
            "Authentication required.",
            hint="Configure a cookie file in Settings.",
        )
    if any(term in message for term in ("timed out", "temporary failure", "name resolution", "connection", "network")):
        return NetworkError("Network error while contacting YouTube.", hint="Check your internet connection.")

    return DownloadError(str(exc))


class YTDLPWrapper:
    """Thin, testable wrapper around the yt-dlp library."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ------------------------------------------------------------------
    # Option building
    # ------------------------------------------------------------------
    def _base_opts(self) -> dict[str, Any]:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            # Single-item operations (video/audio/subtitle/thumbnail) must never
            # accidentally expand into an entire playlist just because the URL
            # carries a "&list=..." parameter (common when copying a link while
            # a playlist is playing). Playlist listing explicitly overrides this.
            "noplaylist": True,
            # Do not swallow errors here: every call site wraps download() in
            # its own try/except and needs real exceptions to report failures
            # accurately. Playlist/search listing opts in to ignoreerrors
            # explicitly so one bad entry doesn't break the whole listing.
            "ignoreerrors": False,
            "retries": self.settings.retry_attempts,
            "continuedl": self.settings.resume_downloads,
        }
        if self.settings.cookie_file:
            opts["cookiefile"] = self.settings.cookie_file
        if self.settings.proxy:
            opts["proxy"] = self.settings.proxy
        if self.settings.rate_limit:
            opts["ratelimit"] = self._parse_rate_limit(self.settings.rate_limit)
        if self.settings.sleep_interval:
            opts["sleep_interval"] = self.settings.sleep_interval
            if self.settings.random_delay:
                opts["max_sleep_interval"] = self.settings.sleep_interval * 2
        return opts

    @staticmethod
    def _parse_rate_limit(value: str) -> int:
        """Parse a rate limit string like '1M' or '500K' into bytes/sec."""
        value = value.strip().upper()
        multiplier = 1
        if value.endswith("K"):
            multiplier, value = 1024, value[:-1]
        elif value.endswith("M"):
            multiplier, value = 1024 * 1024, value[:-1]
        try:
            return int(float(value) * multiplier)
        except ValueError:
            return 0

    def build_video_opts(
        self,
        output_dir: Path,
        filename_template: str,
        resolution: str = "best",
        progress_hook: Optional[ProgressHook] = None,
    ) -> dict[str, Any]:
        """Build yt-dlp options for downloading a video as MP4."""
        opts = self._base_opts()
        opts["outtmpl"] = str(output_dir / filename_template)
        opts["merge_output_format"] = "mp4"
        opts["format"] = self._video_format_selector(resolution)
        if is_ffmpeg_available():
            opts["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}]
        if self.settings.embed_metadata:
            opts.setdefault("postprocessors", []).append({"key": "FFmpegMetadata"})
        if self.settings.embed_thumbnail:
            opts["writethumbnail"] = True
            opts.setdefault("postprocessors", []).append(
                {"key": "EmbedThumbnail"}
            )
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]
        self._apply_archive(opts)
        return opts

    def build_audio_opts(
        self,
        output_dir: Path,
        filename_template: str,
        bitrate: str = "best",
        progress_hook: Optional[ProgressHook] = None,
    ) -> dict[str, Any]:
        """Build yt-dlp options for extracting audio as MP3."""
        opts = self._base_opts()
        opts["outtmpl"] = str(output_dir / filename_template)
        opts["format"] = "bestaudio/best"
        quality = "0" if bitrate == "best" else bitrate
        postprocessors: list[dict[str, Any]] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ]
        if self.settings.embed_metadata:
            postprocessors.append({"key": "FFmpegMetadata"})
        if self.settings.embed_thumbnail:
            opts["writethumbnail"] = True
            postprocessors.append({"key": "EmbedThumbnail"})
        opts["postprocessors"] = postprocessors
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]
        self._apply_archive(opts)
        return opts

    def build_subtitle_opts(
        self,
        output_dir: Path,
        filename_template: str,
        languages: list[str],
        auto_generated: bool = False,
        embed: bool = False,
    ) -> dict[str, Any]:
        """Build yt-dlp options for downloading subtitles only."""
        opts = self._base_opts()
        opts["outtmpl"] = str(output_dir / filename_template)
        opts["skip_download"] = not embed
        opts["writesubtitles"] = True
        opts["writeautomaticsub"] = auto_generated
        opts["subtitleslangs"] = languages or ["en"]
        if embed:
            opts["skip_download"] = False
            opts["postprocessors"] = [{"key": "FFmpegEmbedSubtitle"}]
        return opts

    def build_thumbnail_opts(self, output_dir: Path, filename_template: str) -> dict[str, Any]:
        """Build yt-dlp options for downloading thumbnail only."""
        opts = self._base_opts()
        opts["outtmpl"] = str(output_dir / filename_template)
        opts["skip_download"] = True
        opts["writethumbnail"] = True
        return opts

    def _apply_archive(self, opts: dict[str, Any]) -> None:
        if self.settings.skip_existing:
            opts["download_archive"] = self.settings.download_archive_path
        opts["overwrites"] = self.settings.overwrite_existing

    @staticmethod
    def _video_format_selector(resolution: str) -> str:
        """Translate a resolution label into a yt-dlp format selector string.

        Falls back to the closest lower resolution automatically because
        yt-dlp's ``<=`` height selector picks the best available format
        that does not exceed the requested height.
        """
        if resolution in (None, "best"):
            return "bestvideo+bestaudio/best"
        height = RESOLUTION_HEIGHTS.get(resolution)
        if height is None:
            return "bestvideo+bestaudio/best"
        return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

    # ------------------------------------------------------------------
    # Info extraction
    # ------------------------------------------------------------------
    def extract_video_info(self, url: str) -> VideoInfo:
        """Fetch metadata for a single video without downloading it."""
        import yt_dlp

        opts = self._base_opts()
        opts["skip_download"] = True
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(url, download=False)
        except Exception as exc:  # yt_dlp raises its own DownloadError etc.
            raise _translate_exception(exc, url) from exc

        if data is None:
            raise VideoUnavailableError(f"Could not retrieve video info for: {url}")

        formats = [
            FormatInfo(
                format_id=f.get("format_id", ""),
                ext=f.get("ext", ""),
                resolution=f.get("resolution"),
                height=f.get("height"),
                fps=f.get("fps"),
                filesize=f.get("filesize") or f.get("filesize_approx"),
                vcodec=f.get("vcodec"),
                acodec=f.get("acodec"),
                abr=f.get("abr"),
            )
            for f in data.get("formats", [])
        ]

        return VideoInfo(
            id=data.get("id", ""),
            title=data.get("title", "Unknown"),
            url=url,
            uploader=data.get("uploader"),
            duration=data.get("duration"),
            view_count=data.get("view_count"),
            upload_date=data.get("upload_date"),
            description=data.get("description"),
            thumbnail=data.get("thumbnail"),
            formats=formats,
            is_live=bool(data.get("is_live")),
            is_upcoming=data.get("live_status") == "is_upcoming",
            age_limit=data.get("age_limit", 0) or 0,
            availability=data.get("availability"),
            raw=data,
        )

    def extract_playlist_info(self, url: str) -> PlaylistInfo:
        """Fetch metadata for a playlist (flat, without downloading)."""
        import yt_dlp

        opts = self._base_opts()
        opts["extract_flat"] = "in_playlist"
        opts["skip_download"] = True
        opts["noplaylist"] = False
        opts["ignoreerrors"] = True
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(url, download=False)
        except Exception as exc:
            raise _translate_exception(exc, url) from exc

        if data is None or "entries" not in data:
            raise PlaylistUnavailableError(f"Could not retrieve playlist info for: {url}")

        entries = []
        for idx, entry in enumerate(data.get("entries") or [], start=1):
            if entry is None:
                entries.append(
                    PlaylistEntry(index=idx, availability="unavailable")
                )
                continue
            entries.append(
                PlaylistEntry(
                    index=idx,
                    id=entry.get("id"),
                    title=entry.get("title"),
                    url=entry.get("url") or entry.get("webpage_url"),
                    duration=entry.get("duration"),
                    uploader=entry.get("uploader") or entry.get("channel"),
                    upload_date=entry.get("upload_date"),
                    is_live=bool(entry.get("is_live")),
                    is_premiere=entry.get("live_status") == "is_upcoming",
                    availability=entry.get("availability"),
                    raw=entry,
                )
            )

        return PlaylistInfo(
            id=data.get("id", ""),
            title=data.get("title", "Untitled Playlist"),
            url=url,
            uploader=data.get("uploader") or data.get("channel"),
            entries=entries,
        )

    def resolve_stream_url(self, url: str, resolution: str = "best") -> tuple[str, VideoInfo]:
        """Resolve a direct, playable stream URL for external players (e.g. VLC).

        Returns a tuple of (stream_url, video_info). Does not download
        anything; only extracts a direct media URL that a player can open.
        Prefers a single progressive format (video+audio combined) so the
        external player does not need to merge separate streams itself.
        """
        import yt_dlp

        opts = self._base_opts()
        opts["skip_download"] = True
        height = RESOLUTION_HEIGHTS.get(resolution)
        if height:
            opts["format"] = f"best[height<={height}]/best"
        else:
            opts["format"] = "best"

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(url, download=False)
        except Exception as exc:
            raise _translate_exception(exc, url) from exc

        if data is None:
            raise VideoUnavailableError(f"Could not retrieve video info for: {url}")

        stream_url = data.get("url")
        if not stream_url and data.get("requested_formats"):
            # Fell back to a split video+audio format with no single 'url';
            # external players generally cannot merge two URLs, so surface
            # this as a clear error rather than silently playing video-only.
            raise DownloadError(
                "No combined audio+video stream is available for this video at the "
                "requested resolution. Try 'best' or a lower resolution."
            )
        if not stream_url:
            raise DownloadError(f"Could not resolve a playable stream URL for: {url}")

        formats = [
            FormatInfo(
                format_id=f.get("format_id", ""),
                ext=f.get("ext", ""),
                resolution=f.get("resolution"),
                height=f.get("height"),
                fps=f.get("fps"),
                filesize=f.get("filesize") or f.get("filesize_approx"),
                vcodec=f.get("vcodec"),
                acodec=f.get("acodec"),
                abr=f.get("abr"),
            )
            for f in data.get("formats", [])
        ]
        info = VideoInfo(
            id=data.get("id", ""),
            title=data.get("title", "Unknown"),
            url=url,
            uploader=data.get("uploader"),
            duration=data.get("duration"),
            view_count=data.get("view_count"),
            upload_date=data.get("upload_date"),
            description=data.get("description"),
            thumbnail=data.get("thumbnail"),
            formats=formats,
            is_live=bool(data.get("is_live")),
            is_upcoming=data.get("live_status") == "is_upcoming",
            age_limit=data.get("age_limit", 0) or 0,
            availability=data.get("availability"),
        )
        return stream_url, info

    def search(self, query: str, max_results: int = 10) -> list[VideoInfo]:
        """Search YouTube for videos matching ``query``."""
        import yt_dlp

        opts = self._base_opts()
        opts["extract_flat"] = "in_playlist"
        opts["skip_download"] = True
        opts["ignoreerrors"] = True
        search_url = f"ytsearch{max_results}:{query}"
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                data = ydl.extract_info(search_url, download=False)
        except Exception as exc:
            raise _translate_exception(exc, query) from exc

        results = []
        for entry in (data or {}).get("entries") or []:
            if entry is None:
                continue
            results.append(
                VideoInfo(
                    id=entry.get("id", ""),
                    title=entry.get("title", "Unknown"),
                    url=entry.get("url") or entry.get("webpage_url", ""),
                    uploader=entry.get("uploader") or entry.get("channel"),
                    duration=entry.get("duration"),
                    view_count=entry.get("view_count"),
                    upload_date=entry.get("upload_date"),
                    thumbnail=entry.get("thumbnail"),
                    raw=entry,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Downloading
    # ------------------------------------------------------------------
    def download(self, url: str, opts: dict[str, Any]) -> dict[str, Any]:
        """Run a download for ``url`` with the given yt-dlp ``opts``.

        Returns the info dict yt-dlp produced for the downloaded item.
        """
        import yt_dlp

        needs_ffmpeg = any(
            key in opts for key in ("postprocessors", "merge_output_format")
        )
        if needs_ffmpeg and not is_ffmpeg_available():
            raise FFmpegNotFoundError(
                "FFmpeg is required for this operation but was not found.",
                hint="Install FFmpeg and ensure it is on your system PATH.",
            )

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
        except Exception as exc:
            raise _translate_exception(exc, url) from exc

        if info is None:
            # With ignoreerrors=False, a None result here is not a genuine
            # extraction failure (those raise exceptions above). It means
            # yt-dlp silently skipped the item because it is already
            # present in the download archive.
            if opts.get("download_archive"):
                raise AlreadyDownloadedError(
                    f"Already downloaded: {url}",
                    hint="This item is in your download archive. Disable 'skip_existing' in "
                    "Settings, or remove its entry from the archive file, to download it again.",
                )
            raise DownloadError(f"Download produced no result for: {url}")
        return info

    @staticmethod
    def resolve_output_path(info: dict[str, Any]) -> Optional[str]:
        """Best-effort extraction of the final output file path from a yt-dlp info dict.

        For merged/post-processed downloads, the top-level ``filepath``/``_filename``
        keys are often absent; the real path lives in the last ``requested_downloads``
        entry instead.

        Only use this for operations that actually download video/audio
        (``skip_download`` was not set). For thumbnail-only or subtitle-only
        downloads, use :meth:`resolve_thumbnail_path` / :meth:`resolve_subtitle_paths`
        instead, since ``requested_downloads``/``filepath`` still point at the
        (never-downloaded) video in that case.
        """
        path = info.get("filepath") or info.get("_filename")
        if path:
            return path
        requested = info.get("requested_downloads")
        if requested:
            last = requested[-1]
            return last.get("filepath") or last.get("_filename")
        return None

    @staticmethod
    def resolve_thumbnail_path(info: dict[str, Any]) -> Optional[str]:
        """Extract the saved thumbnail file path from a yt-dlp info dict."""
        thumbnails = info.get("thumbnails") or []
        for thumb in reversed(thumbnails):
            path = thumb.get("filepath")
            if path:
                return path
        files_to_move = info.get("__files_to_move") or {}
        if files_to_move:
            return next(iter(files_to_move.values()), None)
        return None

    @staticmethod
    def resolve_subtitle_paths(info: dict[str, Any]) -> list[str]:
        """Extract saved subtitle file paths from a yt-dlp info dict."""
        requested = info.get("requested_subtitles") or {}
        paths = [sub.get("filepath") for sub in requested.values() if sub.get("filepath")]
        if paths:
            return paths
        files_to_move = info.get("__files_to_move") or {}
        return [
            dest
            for dest in files_to_move.values()
            if any(str(dest).endswith(f".{ext}") for ext in ("srt", "vtt"))
        ]
