"""Log level constants (standard Python ``logging`` levels)."""

from __future__ import annotations

import logging

# Numeric levels for setLevel / filtering
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# Name map for config (string -> level)
LEVEL_BY_NAME: dict[str, int] = {
    "DEBUG": DEBUG,
    "INFO": INFO,
    "WARNING": WARNING,
    "ERROR": ERROR,
    "CRITICAL": CRITICAL,
}

DEFAULT_LEVEL = INFO
