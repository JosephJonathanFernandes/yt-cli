"""Application-wide logging configuration.

Keeps terminal output clean (Rich handles that) while writing detailed,
timestamped, rotating logs to disk for debugging and support purposes.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ytdownloader.constants import LOG_DIR

_LOGGER_NAME = "ytdownloader"
_configured = False


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure and return the application logger.

    Safe to call multiple times; only configures handlers once.
    """
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)

    if _configured:
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        return logger

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = LOG_DIR / "ytdownloader.log"
        file_handler: logging.Handler = RotatingFileHandler(
            log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except OSError:
        # If we cannot write logs (permissions, read-only fs), continue
        # silently; the app must never crash because of logging.
        pass

    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    _configured = True
    return logger


def get_logger() -> logging.Logger:
    """Return the shared application logger (configuring it if needed)."""
    return logging.getLogger(_LOGGER_NAME) if _configured else setup_logging()


def log_dir() -> Path:
    """Return the directory where log files are stored."""
    return LOG_DIR
