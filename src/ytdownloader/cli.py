"""Typer-based CLI: interactive app launcher plus non-interactive flags.

Running with no subcommand launches the interactive Rich menu (``app.py``).
Subcommands allow scripting without menus, per the "non-interactive flags
for scripting" requirement.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from ytdownloader import __version__
from ytdownloader.config import get_config_manager
from ytdownloader.constants import (
    DOWNLOAD_TYPE_AUDIO,
    DOWNLOAD_TYPE_VIDEO,
    HISTORY_STATUS_FAILED,
    HISTORY_STATUS_SKIPPED,
    HISTORY_STATUS_SUCCESS,
)
from ytdownloader.exceptions import YTDownloaderError
from ytdownloader.history import get_history_manager
from ytdownloader.logger import setup_logging
from ytdownloader.ui.tables import video_details_table
from ytdownloader.ui.theme import get_theme, make_console

app = typer.Typer(
    name="ytdownloader",
    help="A polished, terminal-based YouTube downloader built on yt-dlp.",
    no_args_is_help=False,
    add_completion=True,
)
console = make_console("dark")


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
    version: bool = typer.Option(False, "--version", help="Show the application version and exit."),
) -> None:
    """Launch the interactive menu when no subcommand is given."""
    setup_logging(verbose=verbose)
    try:
        theme_name = get_config_manager().load().theme
        console.push_theme(get_theme(theme_name))
    except Exception:  # noqa: BLE001 - never let theming break startup
        pass
    if version:
        console.print(f"ytdownloader {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        from ytdownloader.app import App

        App().run()


@app.command()
def download(
    url: str = typer.Argument(..., help="YouTube video URL to download."),
    audio_only: bool = typer.Option(False, "--audio-only", "-a", help="Download audio as MP3 instead of video."),
    resolution: str = typer.Option("best", "--resolution", "-r", help="Video resolution (e.g. 1080p)."),
    bitrate: str = typer.Option("best", "--bitrate", "-b", help="Audio bitrate in kbps (e.g. 192)."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Fetch and display info without downloading."),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output."),
) -> None:
    """Download a single video or its audio, non-interactively."""
    from ytdownloader.audio import download_audio
    from ytdownloader.video import download_video, fetch_video_info

    config_manager = get_config_manager()
    settings = config_manager.load()
    out_dir = output or Path(settings.output_dir)

    try:
        info = fetch_video_info(settings, url)
    except YTDownloaderError as exc:
        console.print(f"[red]Error:[/red] {exc.message}")
        raise typer.Exit(code=1)

    if not quiet:
        console.print(video_details_table(info))

    if dry_run:
        raise typer.Exit(code=0)

    out_dir.mkdir(parents=True, exist_ok=True)
    if audio_only:
        result = download_audio(settings, info, bitrate, out_dir)
    else:
        result = download_video(settings, info, resolution, out_dir)

    history = get_history_manager()
    from ytdownloader.models import HistoryRecord
    import uuid

    if result.success and result.skipped:
        status = HISTORY_STATUS_SKIPPED
    elif result.success:
        status = HISTORY_STATUS_SUCCESS
    else:
        status = HISTORY_STATUS_FAILED

    history.add(
        HistoryRecord(
            id=str(uuid.uuid4()),
            title=result.title,
            url=result.url,
            type=DOWNLOAD_TYPE_AUDIO if audio_only else DOWNLOAD_TYPE_VIDEO,
            resolution_or_bitrate=bitrate if audio_only else resolution,
            output_path=result.output_path,
            file_size=result.file_size,
            status=status,
            error_message=result.error_message,
        )
    )

    if result.success and result.skipped:
        if not quiet:
            console.print(f"[yellow]Already downloaded (skipped):[/yellow] {result.title}")
    elif result.success:
        if not quiet:
            console.print(f"[green]Downloaded:[/green] {result.output_path}")
    else:
        console.print(f"[red]Failed:[/red] {result.error_message}")
        raise typer.Exit(code=1)


@app.command()
def batch(
    file: Path = typer.Argument(..., help="Path to a text/CSV/JSON file of URLs, or '-' for stdin."),
    audio_only: bool = typer.Option(False, "--audio-only", "-a"),
    resolution: str = typer.Option("best", "--resolution", "-r"),
    bitrate: str = typer.Option("best", "--bitrate", "-b"),
    output: Optional[Path] = typer.Option(None, "--output", "-o"),
) -> None:
    """Download a batch of URLs from a file or stdin, non-interactively."""
    from ytdownloader.audio import download_audio
    from ytdownloader.batch import parse_batch_file, parse_lines
    from ytdownloader.video import download_video, fetch_video_info

    config_manager = get_config_manager()
    settings = config_manager.load()
    out_dir = output or Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if str(file) == "-":
        parse_result = parse_lines(sys.stdin.read()).dedupe()
    else:
        parse_result = parse_batch_file(file)

    console.print(f"{len(parse_result.valid_urls)} valid URLs, {len(parse_result.invalid_lines)} invalid.")

    succeeded = skipped = failed = 0
    for url in parse_result.valid_urls:
        try:
            info = fetch_video_info(settings, url)
            result = (
                download_audio(settings, info, bitrate, out_dir)
                if audio_only
                else download_video(settings, info, resolution, out_dir)
            )
            if result.success and result.skipped:
                skipped += 1
                console.print(f"[yellow]SKIP[/yellow] {info.title} (already downloaded)")
            elif result.success:
                succeeded += 1
                console.print(f"[green]OK[/green] {info.title}")
            else:
                failed += 1
                console.print(f"[red]FAIL[/red] {info.title}: {result.error_message}")
        except YTDownloaderError as exc:
            failed += 1
            console.print(f"[red]FAIL[/red] {url}: {exc.message}")

    console.print(f"Done. {succeeded} succeeded, {skipped} skipped, {failed} failed.")
    if failed and not succeeded and not skipped:
        raise typer.Exit(code=1)


@app.command()
def watch(
    query: str = typer.Argument(..., help="YouTube URL or search query to play."),
    resolution: str = typer.Option("best", "--resolution", "-r", help="Preferred resolution (e.g. 1080p)."),
) -> None:
    """Stream a video directly to VLC without downloading it, non-interactively.

    If QUERY is not a YouTube URL, the top search result is played.
    """
    from ytdownloader.exceptions import YTDownloaderError
    from ytdownloader.search import search_youtube
    from ytdownloader.stream import play_in_vlc, resolve_stream
    from ytdownloader.validators import is_valid_youtube_url, normalize_url

    config_manager = get_config_manager()
    settings = config_manager.load()

    if is_valid_youtube_url(query):
        url = normalize_url(query)
    else:
        try:
            results = search_youtube(settings, query, max_results=1)
        except YTDownloaderError as exc:
            console.print(f"[red]Error:[/red] {exc.message}")
            raise typer.Exit(code=1)
        if not results:
            console.print("[red]No results found.[/red]")
            raise typer.Exit(code=1)
        url = results[0].url

    try:
        stream_url, info = resolve_stream(settings, url, resolution)
        play_in_vlc(stream_url, info.title)
    except YTDownloaderError as exc:
        console.print(f"[red]Error:[/red] {exc.message}")
        if exc.hint:
            console.print(f"[yellow]Hint:[/yellow] {exc.hint}")
        raise typer.Exit(code=1)

    console.print(f"[green]Playing in VLC:[/green] {info.title}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query."),
    max_results: int = typer.Option(10, "--max-results", "-n"),
) -> None:
    """Search YouTube and print results as a table (non-interactive)."""
    from ytdownloader.search import search_youtube
    from ytdownloader.ui.tables import search_results_table

    config_manager = get_config_manager()
    settings = config_manager.load()
    try:
        results = search_youtube(settings, query, max_results)
    except YTDownloaderError as exc:
        console.print(f"[red]Error:[/red] {exc.message}")
        raise typer.Exit(code=1)
    console.print(search_results_table(results))


@app.command()
def history(
    export: Optional[Path] = typer.Option(None, "--export", help="Export history to this path (.json or .csv)."),
) -> None:
    """View or export download history (non-interactive)."""
    hm = get_history_manager()
    if export:
        if export.suffix.lower() == ".csv":
            hm.export_csv(export)
        else:
            hm.export_json(export)
        console.print(f"[green]Exported to {export}[/green]")
        return
    from ytdownloader.ui.tables import history_table

    console.print(history_table(hm.load_all()))


def run() -> None:
    """Entry point invoked by console_scripts."""
    app()
