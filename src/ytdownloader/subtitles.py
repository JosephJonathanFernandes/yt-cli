"""Subtitle download orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ytdownloader.constants import DEFAULT_FILENAME_TEMPLATE
from ytdownloader.downloader import YTDLPWrapper
from ytdownloader.models import DownloadResult, Settings, VideoInfo


def download_subtitles(
    settings: Settings,
    info: VideoInfo,
    languages: Optional[list[str]] = None,
    auto_generated: bool = False,
    embed: bool = False,
    output_dir: Optional[Path] = None,
    filename_template: Optional[str] = None,
) -> DownloadResult:
    """Download subtitles for ``info``, optionally embedding into the video."""
    wrapper = YTDLPWrapper(settings)
    out_dir = output_dir or Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    template = filename_template or settings.filename_template or DEFAULT_FILENAME_TEMPLATE
    langs = languages or settings.subtitle_languages

    opts = wrapper.build_subtitle_opts(out_dir, template, langs, auto_generated, embed)

    try:
        result_info = wrapper.download(info.url, opts)
    except Exception as exc:
        return DownloadResult(
            success=False, title=info.title, url=info.url, error_message=str(exc)
        )

    if embed:
        output_path = wrapper.resolve_output_path(result_info)
    else:
        subtitle_paths = wrapper.resolve_subtitle_paths(result_info)
        output_path = subtitle_paths[0] if subtitle_paths else None
    return DownloadResult(
        success=True,
        title=info.title,
        url=info.url,
        output_path=str(output_path) if output_path else None,
    )
