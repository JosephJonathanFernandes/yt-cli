"""Application entry point used by console_scripts and ``python -m ytdownloader``."""

from __future__ import annotations

import sys


def _ensure_utf8_output() -> None:
    """Force stdout/stderr to UTF-8 so titles with emoji or other non-ASCII
    characters never crash the app.

    On Windows, Python's stdout/stderr default to the system codepage
    (commonly cp1252) whenever output is not attached to a real console
    (e.g. when piped, redirected to a file, or run under some terminal
    hosts). That codepage cannot represent most emoji, which are common
    in real YouTube video titles. ``reconfigure`` is available on Python
    3.7+; wrapped defensively since some non-standard stream types may
    not support it.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def main() -> None:
    """Run the CLI, ensuring the whole app never crashes with a raw traceback."""
    _ensure_utf8_output()

    from ytdownloader.cli import run
    from ytdownloader.logger import get_logger

    try:
        run()
    except KeyboardInterrupt:
        print("\nInterrupted. Goodbye!")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001 - final safety net
        logger = get_logger()
        logger.exception("Fatal unhandled exception")
        print(f"A fatal error occurred: {exc}")
        print("See the log file in ~/.ytdownloader/logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
