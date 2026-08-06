"""Thumbnail download orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ytdownloader.constants import DEFAULT_FILENAME_TEMPLATE
from ytdownloader.downloader import YTDLPWrapper
from ytdownloader.models import DownloadResult, Settings, VideoInfo


def download_thumbnail(
    settings: Settings,
    info: VideoInfo,
    output_dir: Optional[Path] = None,
    filename_template: Optional[str] = None,
) -> DownloadResult:
    """Download the thumbnail image for ``info`` without downloading the video."""
    wrapper = YTDLPWrapper(settings)
    out_dir = output_dir or Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    template = filename_template or settings.filename_template or DEFAULT_FILENAME_TEMPLATE

    opts = wrapper.build_thumbnail_opts(out_dir, template)

    try:
        result_info = wrapper.download(info.url, opts)
    except Exception as exc:
        return DownloadResult(
            success=False, title=info.title, url=info.url, error_message=str(exc)
        )

    output_path = wrapper.resolve_thumbnail_path(result_info)
    return DownloadResult(
        success=True,
        title=info.title,
        url=info.url,
        output_path=str(output_path) if output_path else None,
    )
