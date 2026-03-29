"""Basic file logger: write to a file only at a configured level."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from src.core.logger.log_levels import DEFAULT_LEVEL, LEVEL_BY_NAME


def _resolve_level(level: int | str) -> int:
    """Map config level (string or int) to an int."""
    if isinstance(level, int):
        return level
    s = (level or "").strip().upper()
    return LEVEL_BY_NAME.get(s, DEFAULT_LEVEL)


def _format_msg(msg: Any, *args: Any, **kwargs: Any) -> str:
    if args or kwargs:
        try:
            return str(msg) % args if args else str(msg) % kwargs
        except (TypeError, KeyError):
            return str(msg)
    return str(msg)


class FileLogger:
    """
    Logger implementation that writes to a file.
    No console sink, print, or GUI specifics.
    """

    def __init__(
        self,
        logs_dir: str | Path,
        file_name: str,
        level: int | str = DEFAULT_LEVEL,
    ) -> None:
        self._logs_dir = Path(logs_dir)
        self._file_name = (file_name or "app").strip()
        if self._file_name.endswith(".log"):
            self._file_name = self._file_name[:-4]
        if not self._file_name:
            self._file_name = "app"
        self._level = _resolve_level(level)
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        self._logger, self._file_handler = self._configure()

    def set_level(self, level: int | str) -> None:
        """Change log level without recreating the logger."""
        self._level = _resolve_level(level)
        self._file_handler.setLevel(self._level)

    def _configure(self) -> tuple[logging.Logger, logging.Handler]:
        # Unique name per instance so different paths do not share one logging.Logger
        name = f"file.{id(self)}.{self._file_name}"
        logger = logging.getLogger(name)
        if logger.handlers:
            return logger, logger.handlers[0]
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(
            self._logs_dir / f"{self._file_name}.log",
            encoding="utf-8",
        )
        file_handler.setLevel(self._level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger, file_handler

    def _should_log(self, level: int) -> bool:
        return level >= self._level

    def _log(self, level: int, level_name: str, msg: Any, *args: Any, **kwargs: Any) -> None:
        getattr(self._logger, level_name.lower())(msg, *args, **kwargs)

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, "DEBUG", msg, *args, **kwargs)

    def info(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, "INFO", msg, *args, **kwargs)

    def warning(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, "WARNING", msg, *args, **kwargs)

    def error(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, "ERROR", msg, *args, **kwargs)

    def exception(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        self._logger.exception(str(msg), *args, **kwargs)
