"""Interactive application loop: wires menus, prompts, and business logic together."""

from __future__ import annotations

import traceback
import uuid
from pathlib import Path
from typing import Optional

from ytdownloader.audio import download_audio
from ytdownloader.config import get_config_manager
from ytdownloader.constants import (
    AUDIO_BITRATES,
    DOWNLOAD_TYPE_AUDIO,
    DOWNLOAD_TYPE_PLAYLIST_AUDIO,
    DOWNLOAD_TYPE_PLAYLIST_VIDEO,
    DOWNLOAD_TYPE_SUBTITLE,
    DOWNLOAD_TYPE_THUMBNAIL,
    DOWNLOAD_TYPE_VIDEO,
    HISTORY_STATUS_FAILED,
    HISTORY_STATUS_SKIPPED,
    HISTORY_STATUS_SUCCESS,
    MIN_FREE_DISK_SPACE_MB,
    VIDEO_RESOLUTIONS,
)
from ytdownloader.exceptions import YTDownloaderError
from ytdownloader.filters import apply_filters
from ytdownloader.history import get_history_manager
from ytdownloader.logger import get_logger
from ytdownloader.models import HistoryRecord, PlaylistFilters, Settings
from ytdownloader.playlist import (
    download_playlist_entries,
    fetch_playlist_info,
)
from ytdownloader.progress import build_progress
from ytdownloader.prompts import (
    prompt_choice,
    prompt_confirm,
    prompt_int,
    prompt_path,
    prompt_text,
    prompt_url,
)
from ytdownloader.search import search_youtube
from ytdownloader.stream import play_in_vlc, resolve_stream
from ytdownloader.subtitles import download_subtitles
from ytdownloader.thumbnails import download_thumbnail
from ytdownloader.ui.menu import MAIN_MENU_ITEMS, render_header, render_main_menu
from ytdownloader.ui.tables import (
    formats_table,
    history_table,
    playlist_entries_table,
    search_results_table,
    video_details_table,
)
from ytdownloader.ui.theme import get_theme, make_console
from ytdownloader.utils import get_free_disk_space_mb, open_file_or_folder
from ytdownloader.validators import is_playlist_url, is_valid_youtube_url, normalize_url, parse_index_range
from ytdownloader.video import download_video

logger = get_logger()


class App:
    """Top-level interactive application controller."""

    def __init__(self) -> None:
        self.config_manager = get_config_manager()
        self.settings: Settings = self.config_manager.load()
        self.console = make_console(self.settings.theme)
        self.history_manager = get_history_manager()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Run the main interactive menu loop until the user exits."""
        while True:
            try:
                self.console.clear()
                render_main_menu(self.console)
                choice = prompt_choice(
                    self.console,
                    "Choose an option",
                    [num for num, _ in MAIN_MENU_ITEMS],
                    default="1",
                )
                if choice is None:
                    choice = "13"
                self._dispatch(choice)
            except KeyboardInterrupt:
                self.console.print("\n[warning]Interrupted. Returning to main menu...[/warning]")
                if not prompt_confirm(self.console, "Exit application?", default=False):
                    continue
                self.console.print("[info]Goodbye![/info]")
                return
            except YTDownloaderError as exc:
                self._show_error(exc)
            except Exception as exc:  # noqa: BLE001 - top-level safety net
                logger.error("Unhandled exception: %s", traceback.format_exc())
                self.console.print(f"[error]Unexpected error:[/error] {exc}")
                self.console.print("[muted]Details were written to the log file.[/muted]")

    def _dispatch(self, choice: str) -> None:
        handlers = {
            "1": self.download_single_video,
            "2": self.download_playlist,
            "3": self.download_audio_menu,
            "4": self.download_playlist_audio,
            "5": self.download_subtitles_menu,
            "6": self.download_thumbnail_menu,
            "7": self.batch_download_menu,
            "8": self.search_menu,
            "9": self.watch_menu,
            "10": self.settings_menu,
            "11": self.history_menu,
            "12": self.help_menu,
            "13": self.exit_app,
        }
        handler = handlers.get(choice)
        if handler:
            handler()

    def exit_app(self) -> None:
        """Exit the application."""
        self.console.print("[info]Goodbye![/info]")
        raise SystemExit(0)

    def _show_error(self, exc: YTDownloaderError) -> None:
        self.console.print(f"[error]Error:[/error] {exc.message}")
        if exc.hint:
            self.console.print(f"[muted]Hint: {exc.hint}[/muted]")
        logger.error("Handled error: %s", exc.message)

    def _check_disk_space(self, output_dir: Path) -> bool:
        free_mb = get_free_disk_space_mb(output_dir)
        if free_mb < MIN_FREE_DISK_SPACE_MB:
            self.console.print(
                f"[warning]Low disk space: only {free_mb:.0f} MB free at {output_dir}.[/warning]"
            )
            return prompt_confirm(self.console, "Continue anyway?", default=False)
        return True

    def _record_history(
        self,
        title: str,
        url: str,
        type_: str,
        status: str,
        resolution_or_bitrate: Optional[str] = None,
        output_path: Optional[str] = None,
        file_size: Optional[int] = None,
        error_message: Optional[str] = None,
        playlist_name: Optional[str] = None,
    ) -> None:
        record = HistoryRecord(
            id=str(uuid.uuid4()),
            title=title,
            url=url,
            type=type_,
            resolution_or_bitrate=resolution_or_bitrate,
            output_path=output_path,
            file_size=file_size,
            status=status,
            error_message=error_message,
            playlist_name=playlist_name,
        )
        self.history_manager.add(record)

    # ------------------------------------------------------------------
    # 1. Download Single Video
    # ------------------------------------------------------------------
    def download_single_video(self) -> None:
        render_header(self.console, "Download Single Video")
        url = prompt_url(self.console)
        if url is None:
            return

        with self.console.status("[info]Fetching video info...[/info]"):
            info = self._fetch_video_info_safe(url)
        if info is None:
            return

        self.console.print(video_details_table(info))
        if info.formats:
            self.console.print(formats_table(info.formats))

        action = prompt_choice(
            self.console,
            "Download as",
            ["mp4", "mp3", "subtitles", "thumbnail", "metadata"],
            default="mp4",
        )
        if action is None:
            return

        output_dir = Path(self.settings.output_dir)
        if not self._check_disk_space(output_dir):
            return

        if action == "mp4":
            resolution = prompt_choice(self.console, "Resolution", VIDEO_RESOLUTIONS, default="best")
            if resolution is None:
                return
            with build_progress() as progress:
                result = download_video(self.settings, info, resolution, output_dir, progress=progress)
            self._finish_result(result, DOWNLOAD_TYPE_VIDEO, resolution)
        elif action == "mp3":
            bitrate = prompt_choice(self.console, "Bitrate (kbps)", AUDIO_BITRATES, default="best")
            if bitrate is None:
                return
            with build_progress() as progress:
                result = download_audio(self.settings, info, bitrate, output_dir, progress=progress)
            self._finish_result(result, DOWNLOAD_TYPE_AUDIO, bitrate)
        elif action == "subtitles":
            self._download_subtitles_for(info, output_dir)
        elif action == "thumbnail":
            result = download_thumbnail(self.settings, info, output_dir)
            self._finish_result(result, DOWNLOAD_TYPE_THUMBNAIL)
        elif action == "metadata":
            self._export_metadata(info, output_dir)

    def _fetch_video_info_safe(self, url: str):
        from ytdownloader.video import fetch_video_info

        try:
            return fetch_video_info(self.settings, url)
        except YTDownloaderError as exc:
            self._show_error(exc)
            return None

    def _finish_result(self, result, type_: str, quality: Optional[str] = None) -> None:
        if result.success and result.skipped:
            self.console.print(f"[warning]Already downloaded (skipped):[/warning] {result.title}")
            self._record_history(
                result.title, result.url, type_, HISTORY_STATUS_SKIPPED,
                quality, result.output_path, result.file_size,
            )
        elif result.success:
            self.console.print(f"[success]Downloaded:[/success] {result.title}")
            if result.output_path:
                self.console.print(f"[muted]Saved to: {result.output_path}[/muted]")
                if prompt_confirm(self.console, "Open output file/folder?", default=False):
                    open_file_or_folder(Path(result.output_path).parent)
            self._record_history(
                result.title, result.url, type_, HISTORY_STATUS_SUCCESS,
                quality, result.output_path, result.file_size,
            )
        else:
            self.console.print(f"[error]Failed:[/error] {result.title} - {result.error_message}")
            self._record_history(
                result.title, result.url, type_, HISTORY_STATUS_FAILED,
                quality, error_message=result.error_message,
            )

    def _download_subtitles_for(self, info, output_dir: Path) -> None:
        langs_raw = prompt_text(self.console, "Language codes (comma separated)", default="en")
        if langs_raw is None:
            return
        languages = [x.strip() for x in langs_raw.split(",") if x.strip()]
        auto = prompt_confirm(self.console, "Include auto-generated subtitles?", default=False)
        embed = prompt_confirm(self.console, "Embed subtitles into video?", default=False)
        result = download_subtitles(self.settings, info, languages, auto, embed, output_dir)
        self._finish_result(result, DOWNLOAD_TYPE_SUBTITLE, ",".join(languages))

    def _export_metadata(self, info, output_dir: Path) -> None:
        from ytdownloader.utils import sanitize_filename

        dest = output_dir / f"{sanitize_filename(info.title)}.info.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        dest.write_text(info.model_dump_json(indent=2), encoding="utf-8")
        self.console.print(f"[success]Metadata saved to:[/success] {dest}")

    # ------------------------------------------------------------------
    # 2. Download Playlist / 4. Playlist as MP3
    # ------------------------------------------------------------------
    def download_playlist(self, force_audio: bool = False) -> None:
        render_header(self.console, "Download Playlist" + (" as MP3" if force_audio else ""))
        url = prompt_url(self.console, "Enter playlist URL")
        if url is None:
            return
        if not is_playlist_url(url):
            self.console.print("[warning]This does not look like a playlist URL, continuing anyway.[/warning]")

        with self.console.status("[info]Analyzing playlist...[/info]"):
            try:
                playlist = fetch_playlist_info(self.settings, url)
            except YTDownloaderError as exc:
                self._show_error(exc)
                return

        self.console.print(
            f"[title]{playlist.title}[/title]  [muted]by {playlist.uploader or 'Unknown'}[/muted]"
        )
        self.console.print(
            f"Total videos: {playlist.total_videos}  |  "
            f"Unavailable: {playlist.unavailable_count}"
        )
        self.console.print(playlist_entries_table(playlist.entries))

        range_choice = prompt_choice(
            self.console,
            "Select range",
            ["all", "first_n", "last_n", "range", "custom"],
            default="all",
        )
        if range_choice is None:
            return

        entries = playlist.entries
        if range_choice == "first_n":
            n = prompt_int(self.console, "Number of videos from start", default=10, min_value=1)
            if n is None:
                return
            entries = entries[:n]
        elif range_choice == "last_n":
            n = prompt_int(self.console, "Number of videos from end", default=10, min_value=1)
            if n is None:
                return
            entries = entries[-n:]
        elif range_choice in ("range", "custom"):
            spec = prompt_text(self.console, "Enter indices (e.g. 25-60 or 1,3,5)")
            if spec is None:
                return
            try:
                indices = parse_index_range(spec, len(entries))
            except ValueError as exc:
                self.console.print(f"[warning]{exc}[/warning]")
                return
            index_set = set(indices)
            entries = [e for e in entries if e.index in index_set]

        if prompt_confirm(self.console, "Apply advanced filters?", default=False):
            filters = self._prompt_playlist_filters()
            if filters is not None:
                entries = apply_filters(entries, filters)

        self.console.print(f"[info]{len(entries)} videos selected after filtering.[/info]")
        if not entries:
            self.console.print("[warning]No videos match the current selection/filters.[/warning]")
            return

        output_type = "mp3" if force_audio else prompt_choice(
            self.console, "Output type", ["mp4", "mp3", "subtitles", "thumbnail", "metadata"], default="mp4"
        )
        if output_type is None:
            return

        output_dir = Path(self.settings.output_dir) / self.__class__._safe_dir(playlist.title)
        if not self._check_disk_space(output_dir):
            return

        if not prompt_confirm(
            self.console, f"Download {len(entries)} videos to {output_dir}?", default=True
        ):
            return

        resolution, bitrate = "best", "best"
        if output_type == "mp4":
            resolution = prompt_choice(self.console, "Resolution", VIDEO_RESOLUTIONS, default="best") or "best"
        elif output_type == "mp3":
            bitrate = prompt_choice(self.console, "Bitrate (kbps)", AUDIO_BITRATES, default="best") or "best"

        if output_type in ("mp4", "mp3"):
            with build_progress() as progress:
                results = download_playlist_entries(
                    self.settings, entries, output_type, resolution, bitrate, output_dir, progress
                )
            self._summarize_playlist_results(
                results, playlist.title,
                DOWNLOAD_TYPE_PLAYLIST_AUDIO if output_type == "mp3" else DOWNLOAD_TYPE_PLAYLIST_VIDEO,
                bitrate if output_type == "mp3" else resolution,
            )
        elif output_type == "subtitles":
            self._batch_subtitles(entries, output_dir, playlist.title)
        elif output_type == "thumbnail":
            self._batch_thumbnails(entries, output_dir, playlist.title)
        elif output_type == "metadata":
            self._batch_metadata(entries, output_dir)

    @staticmethod
    def _safe_dir(name: str) -> str:
        from ytdownloader.utils import sanitize_filename

        return sanitize_filename(name)

    def download_playlist_audio(self) -> None:
        """Shortcut for menu option 4: download an entire playlist as MP3."""
        self.download_playlist(force_audio=True)

    def _prompt_playlist_filters(self) -> Optional[PlaylistFilters]:
        min_dur = prompt_int(self.console, "Minimum duration (seconds, 0 for none)", default=0, min_value=0)
        if min_dur is None:
            return None
        max_dur = prompt_int(self.console, "Maximum duration (seconds, 0 for none)", default=0, min_value=0)
        if max_dur is None:
            return None
        skip_shorts = prompt_confirm(self.console, "Skip Shorts (<=60s)?", default=False)
        skip_live = prompt_confirm(self.console, "Skip live streams?", default=False)
        skip_premieres = prompt_confirm(self.console, "Skip premieres?", default=False)
        include_kw = prompt_text(self.console, "Include keyword filter (comma separated, blank for none)", default="", allow_empty=True)
        exclude_kw = prompt_text(self.console, "Exclude keyword filter (comma separated, blank for none)", default="", allow_empty=True)

        return PlaylistFilters(
            min_duration=min_dur or None,
            max_duration=max_dur or None,
            skip_shorts=skip_shorts,
            skip_live=skip_live,
            skip_premieres=skip_premieres,
            include_keywords=[k.strip() for k in (include_kw or "").split(",") if k.strip()],
            exclude_keywords=[k.strip() for k in (exclude_kw or "").split(",") if k.strip()],
        )

    def _summarize_playlist_results(self, results, playlist_name, type_, quality) -> None:
        succeeded = sum(1 for r in results if r.success and not r.skipped)
        skipped = sum(1 for r in results if r.success and r.skipped)
        failed = len(results) - succeeded - skipped
        self.console.print(
            f"[success]{succeeded} succeeded[/success], "
            f"[warning]{skipped} skipped[/warning], "
            f"[error]{failed} failed[/error] out of {len(results)}."
        )
        for r in results:
            if r.success and r.skipped:
                status = HISTORY_STATUS_SKIPPED
            elif r.success:
                status = HISTORY_STATUS_SUCCESS
            else:
                status = HISTORY_STATUS_FAILED
            self._record_history(
                r.title, r.url, type_, status, quality, r.output_path, r.file_size,
                r.error_message, playlist_name=playlist_name,
            )

    def _batch_subtitles(self, entries, output_dir, playlist_name) -> None:
        from ytdownloader.playlist import entry_to_video_info

        langs_raw = prompt_text(self.console, "Language codes (comma separated)", default="en")
        if langs_raw is None:
            return
        languages = [x.strip() for x in langs_raw.split(",") if x.strip()]
        for entry in entries:
            info = entry_to_video_info(entry)
            if not info.url:
                continue
            result = download_subtitles(self.settings, info, languages, output_dir=output_dir)
            status = HISTORY_STATUS_SUCCESS if result.success else HISTORY_STATUS_FAILED
            self._record_history(
                result.title, result.url, DOWNLOAD_TYPE_SUBTITLE, status,
                ",".join(languages), result.output_path, playlist_name=playlist_name,
            )
        self.console.print("[success]Subtitle batch complete.[/success]")

    def _batch_thumbnails(self, entries, output_dir, playlist_name) -> None:
        from ytdownloader.playlist import entry_to_video_info

        for entry in entries:
            info = entry_to_video_info(entry)
            if not info.url:
                continue
            result = download_thumbnail(self.settings, info, output_dir)
            status = HISTORY_STATUS_SUCCESS if result.success else HISTORY_STATUS_FAILED
            self._record_history(
                result.title, result.url, DOWNLOAD_TYPE_THUMBNAIL, status,
                output_path=result.output_path, playlist_name=playlist_name,
            )
        self.console.print("[success]Thumbnail batch complete.[/success]")

    def _batch_metadata(self, entries, output_dir) -> None:
        from ytdownloader.playlist import entry_to_video_info

        output_dir.mkdir(parents=True, exist_ok=True)
        for entry in entries:
            info = entry_to_video_info(entry)
            self._export_metadata(info, output_dir)
        self.console.print("[success]Metadata export complete.[/success]")

    # ------------------------------------------------------------------
    # 3. Download Audio (MP3) - standalone shortcut
    # ------------------------------------------------------------------
    def download_audio_menu(self) -> None:
        render_header(self.console, "Download Audio (MP3)")
        url = prompt_url(self.console)
        if url is None:
            return
        with self.console.status("[info]Fetching video info...[/info]"):
            info = self._fetch_video_info_safe(url)
        if info is None:
            return
        self.console.print(video_details_table(info))
        bitrate = prompt_choice(self.console, "Bitrate (kbps)", AUDIO_BITRATES, default="best")
        if bitrate is None:
            return
        output_dir = Path(self.settings.output_dir)
        if not self._check_disk_space(output_dir):
            return
        with build_progress() as progress:
            result = download_audio(self.settings, info, bitrate, output_dir, progress=progress)
        self._finish_result(result, DOWNLOAD_TYPE_AUDIO, bitrate)

    # ------------------------------------------------------------------
    # 5. Download Subtitles - standalone
    # ------------------------------------------------------------------
    def download_subtitles_menu(self) -> None:
        render_header(self.console, "Download Subtitles")
        url = prompt_url(self.console)
        if url is None:
            return
        with self.console.status("[info]Fetching video info...[/info]"):
            info = self._fetch_video_info_safe(url)
        if info is None:
            return
        self.console.print(video_details_table(info))
        self._download_subtitles_for(info, Path(self.settings.output_dir))

    # ------------------------------------------------------------------
    # 6. Download Thumbnail - standalone
    # ------------------------------------------------------------------
    def download_thumbnail_menu(self) -> None:
        render_header(self.console, "Download Thumbnail")
        url = prompt_url(self.console)
        if url is None:
            return
        with self.console.status("[info]Fetching video info...[/info]"):
            info = self._fetch_video_info_safe(url)
        if info is None:
            return
        self.console.print(video_details_table(info))
        result = download_thumbnail(self.settings, info, Path(self.settings.output_dir))
        self._finish_result(result, DOWNLOAD_TYPE_THUMBNAIL)

    # ------------------------------------------------------------------
    # 7. Batch Download from File
    # ------------------------------------------------------------------
    def batch_download_menu(self) -> None:
        from ytdownloader.batch import BatchSummary, parse_batch_file, parse_lines

        render_header(self.console, "Batch Download from File")
        source = prompt_choice(self.console, "Source", ["file", "paste"], default="file")
        if source is None:
            return

        if source == "file":
            path = prompt_path(self.console, "Path to batch file (.txt/.csv/.json)", must_exist=True)
            if path is None:
                return
            parse_result = parse_batch_file(path)
        else:
            self.console.print("[info]Paste URLs (one per line). Submit an empty line to finish.[/info]")
            lines = []
            while True:
                line = prompt_text(self.console, "URL (blank to finish)", allow_empty=True)
                if line is None:
                    return
                if not line:
                    break
                lines.append(line)
            parse_result = parse_lines("\n".join(lines)).dedupe()

        if parse_result.invalid_lines:
            self.console.print(f"[warning]{len(parse_result.invalid_lines)} invalid entries skipped.[/warning]")
        if not parse_result.valid_urls:
            self.console.print("[error]No valid URLs found.[/error]")
            return

        self.console.print(f"[info]{len(parse_result.valid_urls)} valid URLs found.[/info]")
        output_type = prompt_choice(self.console, "Download as", ["mp4", "mp3"], default="mp4")
        if output_type is None:
            return
        resolution, bitrate = "best", "best"
        if output_type == "mp4":
            resolution = prompt_choice(self.console, "Resolution", VIDEO_RESOLUTIONS, default="best") or "best"
        else:
            bitrate = prompt_choice(self.console, "Bitrate (kbps)", AUDIO_BITRATES, default="best") or "best"

        output_dir = Path(self.settings.output_dir)
        if not self._check_disk_space(output_dir):
            return

        summary = BatchSummary()
        with build_progress() as progress:
            for idx, url in enumerate(parse_result.valid_urls, start=1):
                try:
                    info = self._fetch_video_info_safe(url)
                    if info is None:
                        summary.record(False, error=f"{url}: could not fetch info")
                        continue
                    label = f"{idx}/{len(parse_result.valid_urls)}: {info.title[:40]}"
                    if output_type == "mp4":
                        result = download_video(self.settings, info, resolution, output_dir, progress=progress, label=label)
                    else:
                        result = download_audio(self.settings, info, bitrate, output_dir, progress=progress, label=label)
                    self._finish_result_silent(result, DOWNLOAD_TYPE_VIDEO if output_type == "mp4" else DOWNLOAD_TYPE_AUDIO, resolution if output_type == "mp4" else bitrate)
                    summary.record(result.success, skipped=result.skipped, error=result.error_message)
                except YTDownloaderError as exc:
                    summary.record(False, error=exc.message)

        self.console.print(
            f"[success]{summary.succeeded} succeeded[/success], "
            f"[error]{summary.failed} failed[/error], "
            f"[warning]{summary.skipped} skipped[/warning] out of {summary.total}."
        )

    def _finish_result_silent(self, result, type_, quality=None) -> None:
        if result.success and result.skipped:
            status = HISTORY_STATUS_SKIPPED
        elif result.success:
            status = HISTORY_STATUS_SUCCESS
        else:
            status = HISTORY_STATUS_FAILED
        self._record_history(result.title, result.url, type_, status, quality, result.output_path, result.file_size, result.error_message)

    # ------------------------------------------------------------------
    # 8. Search YouTube
    # ------------------------------------------------------------------
    def search_menu(self) -> None:
        render_header(self.console, "Search YouTube")
        query = prompt_text(self.console, "Search query")
        if query is None:
            return
        with self.console.status("[info]Searching...[/info]"):
            try:
                results = search_youtube(self.settings, query, max_results=10)
            except YTDownloaderError as exc:
                self._show_error(exc)
                return
        if not results:
            self.console.print("[warning]No results found.[/warning]")
            return
        self.console.print(search_results_table(results))
        idx = prompt_int(self.console, "Select a result number to download (0 to cancel)", default=0, min_value=0, max_value=len(results))
        if not idx:
            return
        selected = results[idx - 1]
        with self.console.status("[info]Fetching video info...[/info]"):
            info = self._fetch_video_info_safe(selected.url)
        if info is None:
            return
        self.console.print(video_details_table(info))
        action = prompt_choice(self.console, "Download as", ["mp4", "mp3"], default="mp4")
        if action is None:
            return
        output_dir = Path(self.settings.output_dir)
        if action == "mp4":
            resolution = prompt_choice(self.console, "Resolution", VIDEO_RESOLUTIONS, default="best") or "best"
            with build_progress() as progress:
                result = download_video(self.settings, info, resolution, output_dir, progress=progress)
            self._finish_result(result, DOWNLOAD_TYPE_VIDEO, resolution)
        else:
            bitrate = prompt_choice(self.console, "Bitrate (kbps)", AUDIO_BITRATES, default="best") or "best"
            with build_progress() as progress:
                result = download_audio(self.settings, info, bitrate, output_dir, progress=progress)
            self._finish_result(result, DOWNLOAD_TYPE_AUDIO, bitrate)

    # ------------------------------------------------------------------
    # 9. Watch in VLC
    # ------------------------------------------------------------------
    def watch_menu(self) -> None:
        render_header(self.console, "Watch in VLC")
        self.console.print(
            "[muted]Enter a YouTube URL to play it directly, or type a search query to pick from results.[/muted]"
        )
        raw = prompt_text(self.console, "URL or search query")
        if raw is None:
            return

        info = None
        if is_valid_youtube_url(raw):
            url = normalize_url(raw)
            with self.console.status("[info]Fetching video info...[/info]"):
                info = self._fetch_video_info_safe(url)
            if info is None:
                return
        else:
            with self.console.status("[info]Searching...[/info]"):
                try:
                    results = search_youtube(self.settings, raw, max_results=10)
                except YTDownloaderError as exc:
                    self._show_error(exc)
                    return
            if not results:
                self.console.print("[warning]No results found.[/warning]")
                return
            self.console.print(search_results_table(results))
            idx = prompt_int(
                self.console, "Select a result number to watch (0 to cancel)",
                default=0, min_value=0, max_value=len(results),
            )
            if not idx:
                return
            selected = results[idx - 1]
            with self.console.status("[info]Fetching video info...[/info]"):
                info = self._fetch_video_info_safe(selected.url)
            if info is None:
                return

        self.console.print(video_details_table(info))
        resolution = prompt_choice(self.console, "Resolution", VIDEO_RESOLUTIONS, default="best")
        if resolution is None:
            return

        with self.console.status("[info]Resolving stream...[/info]"):
            try:
                stream_url, _ = resolve_stream(self.settings, info.url, resolution)
            except YTDownloaderError as exc:
                self._show_error(exc)
                return

        try:
            play_in_vlc(stream_url, info.title)
        except YTDownloaderError as exc:
            self._show_error(exc)
            return

        self.console.print(f"[success]Playing in VLC:[/success] {info.title}")

    # ------------------------------------------------------------------
    # 10. Settings
    # ------------------------------------------------------------------
    def settings_menu(self) -> None:
        while True:
            render_header(self.console, "Settings")
            choice = prompt_choice(
                self.console,
                "Choose an action",
                ["view", "edit", "reset", "export", "import", "validate", "back"],
                default="view",
            )
            if choice is None or choice == "back":
                return
            if choice == "view":
                self._print_settings()
            elif choice == "edit":
                self._edit_settings()
            elif choice == "reset":
                if prompt_confirm(self.console, "Reset all settings to defaults?", default=False):
                    self.settings = self.config_manager.reset()
                    self.console.print("[success]Settings reset.[/success]")
            elif choice == "export":
                path = prompt_path(self.console, "Export path")
                if path:
                    self.config_manager.export(path)
                    self.console.print(f"[success]Exported to {path}[/success]")
            elif choice == "import":
                path = prompt_path(self.console, "Import path", must_exist=True)
                if path:
                    try:
                        self.settings = self.config_manager.import_from(path)
                        self.console.print("[success]Settings imported.[/success]")
                    except YTDownloaderError as exc:
                        self._show_error(exc)
            elif choice == "validate":
                valid, error = self.config_manager.validate_integrity()
                if valid:
                    self.console.print("[success]Config is valid.[/success]")
                else:
                    self.console.print(f"[error]Config invalid:[/error] {error}")

    def _print_settings(self) -> None:
        for field_name, value in self.settings.model_dump().items():
            self.console.print(f"[info]{field_name}[/info]: {value}")

    def _edit_settings(self) -> None:
        editable_fields = list(Settings.model_fields.keys())
        self.console.print("[info]Editable fields:[/info] " + ", ".join(editable_fields))
        field_name = prompt_text(self.console, "Field to edit")
        if field_name is None:
            return
        field_name = field_name.strip()
        if field_name not in editable_fields:
            self.console.print(f"[warning]Unknown field: {field_name}[/warning]")
            return

        current = getattr(self.settings, field_name)
        field_info = Settings.model_fields[field_name]
        annotation = field_info.annotation
        default_display = self._display_value(current, annotation)
        new_value_raw = prompt_text(
            self.console, f"New value for {field_name}", default=default_display, allow_empty=True
        )
        if new_value_raw is None:
            return

        try:
            new_value = self._coerce_value(annotation, new_value_raw)
            self.settings = self.config_manager.update(**{field_name: new_value})
            self.console.print(f"[success]{field_name} updated.[/success]")
            self.console.theme = get_theme(self.settings.theme)
        except Exception as exc:  # noqa: BLE001
            self.console.print(f"[error]Invalid value:[/error] {exc}")

    @staticmethod
    def _display_value(current, annotation) -> str:
        """Render a setting's current value as editable plain text.

        List values are shown comma-separated (not Python repr) so that
        accepting the default and re-parsing it round-trips correctly.
        """
        import typing

        if typing.get_origin(annotation) is list and isinstance(current, list):
            return ",".join(str(x) for x in current)
        return "" if current is None else str(current)

    @staticmethod
    def _coerce_value(annotation, raw: str):
        import typing

        origin = typing.get_origin(annotation)
        raw = raw.strip()
        if origin is list:
            return [x.strip() for x in raw.split(",") if x.strip()]
        if raw.lower() in ("none", "null", ""):
            return None
        if annotation is bool:
            return raw.lower() in ("1", "true", "yes", "y", "on")
        if annotation is int:
            return int(raw)
        if annotation is float:
            return float(raw)
        return raw

    # ------------------------------------------------------------------
    # 11. Download History
    # ------------------------------------------------------------------
    def history_menu(self) -> None:
        while True:
            render_header(self.console, "Download History")
            choice = prompt_choice(
                self.console,
                "Choose an action",
                ["view", "search", "filter", "delete", "clear", "open", "export", "back"],
                default="view",
            )
            if choice is None or choice == "back":
                return
            if choice == "view":
                records = self.history_manager.load_all()
                self.console.print(history_table(records) if records else "[muted]No history yet.[/muted]")
            elif choice == "search":
                query = prompt_text(self.console, "Search query")
                if query is not None:
                    self.console.print(history_table(self.history_manager.search(query)))
            elif choice == "filter":
                type_ = prompt_text(self.console, "Type filter (blank for any)", allow_empty=True)
                status = prompt_text(self.console, "Status filter (blank for any)", allow_empty=True)
                records = self.history_manager.filter_by(type_ or None, status or None)
                self.console.print(history_table(records))
            elif choice == "delete":
                record_id = prompt_text(self.console, "Record ID to delete")
                if record_id and self.history_manager.delete(record_id):
                    self.console.print("[success]Record deleted.[/success]")
                elif record_id:
                    self.console.print("[warning]Record not found.[/warning]")
            elif choice == "clear":
                if prompt_confirm(self.console, "Clear all history?", default=False):
                    self.history_manager.clear()
                    self.console.print("[success]History cleared.[/success]")
            elif choice == "open":
                record_id = prompt_text(self.console, "Record ID to open")
                if record_id:
                    records = [r for r in self.history_manager.load_all() if r.id == record_id]
                    if records and records[0].output_path:
                        open_file_or_folder(Path(records[0].output_path))
                    else:
                        self.console.print("[warning]Record not found or has no output path.[/warning]")
            elif choice == "export":
                fmt = prompt_choice(self.console, "Export format", ["json", "csv"], default="json")
                path = prompt_path(self.console, "Export path")
                if fmt and path:
                    if fmt == "json":
                        self.history_manager.export_json(path)
                    else:
                        self.history_manager.export_csv(path)
                    self.console.print(f"[success]Exported to {path}[/success]")

    # ------------------------------------------------------------------
    # 12. Help
    # ------------------------------------------------------------------
    def help_menu(self) -> None:
        render_header(self.console, "Help")
        self.console.print(
            "[info]Navigation:[/info] Type 'back' or 'cancel' at any prompt to return to the previous step.\n"
            "[info]Ctrl+C:[/info] Interrupts the current operation and offers to return to the main menu.\n"
            "[info]Watch in VLC:[/info] Menu option 9 streams a video directly to VLC without downloading it. "
            "Enter a URL or a search query; both are auto-detected.\n"
            "[info]Settings:[/info] Configure defaults, proxy, cookies, and rate limits from menu option 10.\n"
            "[info]History:[/info] All downloads are recorded and viewable/searchable from menu option 11.\n"
            "[info]FFmpeg:[/info] Required for MP4 merging and MP3 extraction. Install it and ensure it's on PATH.\n"
            "[info]VLC:[/info] Required for the 'Watch in VLC' feature. Install it and ensure it's on PATH.\n"
        )
        prompt_confirm(self.console, "Return to main menu?", default=True)
