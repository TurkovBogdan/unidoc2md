"""Route log output to console/GUI via a sink callback. Does not write to a file."""

from __future__ import annotations

import logging
from typing import Any, Callable

from src.core.logger.file_logger import _format_msg, _resolve_level
from src.core.logger.log_levels import DEFAULT_LEVEL


class ConsoleLogger:
    """Logger that writes to an arbitrary sink (e.g. GUI widget or stdout)."""

    def __init__(
        self,
        sink: Callable[[str], None],
        level: int | str = DEFAULT_LEVEL,
    ) -> None:
        self._sink = sink
        self._level = _resolve_level(level)

    def set_level(self, level: int | str) -> None:
        self._level = _resolve_level(level)

    def _emit(self, level: int, level_name: str, msg: Any, *args: Any, **kwargs: Any) -> None:
        if level < self._level:
            return
        text = _format_msg(msg, *args, **kwargs)
        self._sink(f"[{level_name}] {text}")

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.DEBUG, "DEBUG", msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.INFO, "INFO", msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.WARNING, "WARNING", msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.ERROR, "ERROR", msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._emit(logging.ERROR, "ERROR", msg, *args, **kwargs)
