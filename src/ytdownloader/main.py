"""Application entry point used by console_scripts and ``python -m ytdownloader``."""

from __future__ import annotations

import sys


def main() -> None:
    """Run the CLI, ensuring the whole app never crashes with a raw traceback."""
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
