"""Single video download orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.progress import Progress

from ytdownloader.constants import DEFAULT_FILENAME_TEMPLATE
from ytdownloader.downloader import YTDLPWrapper
from ytdownloader.exceptions import AlreadyDownloadedError
from ytdownloader.models import DownloadResult, Settings, VideoInfo
from ytdownloader.progress import DownloadProgressReporter, make_progress_hook


def fetch_video_info(settings: Settings, url: str) -> VideoInfo:
    """Fetch metadata for a single video URL."""
    wrapper = YTDLPWrapper(settings)
    return wrapper.extract_video_info(url)


def download_video(
    settings: Settings,
    info: VideoInfo,
    resolution: str = "best",
    output_dir: Optional[Path] = None,
    filename_template: Optional[str] = None,
    progress: Optional[Progress] = None,
    label: str = "Video",
) -> DownloadResult:
    """Download a video as MP4 at the requested resolution."""
    wrapper = YTDLPWrapper(settings)
    out_dir = output_dir or Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    template = filename_template or settings.filename_template or DEFAULT_FILENAME_TEMPLATE

    hook = None
    if progress is not None:
        reporter = DownloadProgressReporter(progress, label)
        hook = make_progress_hook(reporter)

    opts = wrapper.build_video_opts(out_dir, template, resolution, progress_hook=hook)

    try:
        result_info = wrapper.download(info.url, opts)
    except AlreadyDownloadedError as exc:
        return DownloadResult(
            success=True, title=info.title, url=info.url, skipped=True, error_message=exc.message
        )
    except Exception as exc:
        return DownloadResult(
            success=False, title=info.title, url=info.url, error_message=str(exc)
        )

    output_path = wrapper.resolve_output_path(result_info)
    return DownloadResult(
        success=True,
        title=info.title,
        url=info.url,
        output_path=str(output_path) if output_path else None,
        file_size=result_info.get("filesize") or result_info.get("filesize_approx"),
    )


def build_video_output_dir(base_dir: Path) -> Path:
    """Return the sanitized output directory for video downloads."""
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir
