"""Stream-and-play support: resolve a YouTube video to a direct URL and hand
it off to VLC, without downloading anything to disk.
"""

from __future__ import annotations

import subprocess

from ytdownloader.downloader import YTDLPWrapper
from ytdownloader.exceptions import VLCNotFoundError
from ytdownloader.models import Settings, VideoInfo
from ytdownloader.utils import get_vlc_path


def resolve_stream(settings: Settings, url: str, resolution: str = "best") -> tuple[str, VideoInfo]:
    """Resolve ``url`` to a direct, playable stream URL and its video info."""
    wrapper = YTDLPWrapper(settings)
    return wrapper.resolve_stream_url(url, resolution)


def play_in_vlc(stream_url: str, title: str = "") -> subprocess.Popen:
    """Launch VLC pointed at ``stream_url``.

    Returns the launched :class:`subprocess.Popen` handle immediately;
    VLC runs independently and this call does not block. Raises
    :class:`VLCNotFoundError` if VLC cannot be located.
    """
    vlc_path = get_vlc_path()
    if not vlc_path:
        raise VLCNotFoundError(
            "VLC is required to play videos but was not found.",
            hint="Install VLC from https://www.videolan.org/vlc/ and ensure it is on your system PATH.",
        )

    args = [vlc_path, stream_url, "--play-and-exit"]
    if title:
        args += ["--meta-title", title]

    return subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
