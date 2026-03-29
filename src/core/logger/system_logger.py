"""Application system logger: file logger writing to ``logs/system.log``."""

from __future__ import annotations

from pathlib import Path

from src.core.logger.file_logger import FileLogger
from src.core.logger.log_levels import DEFAULT_LEVEL


class SystemLogger(FileLogger):
    """File logger for the application system log."""

    def __init__(
        self,
        logs_dir: str | Path,
        file_name: str = "system",
        level: int | str = DEFAULT_LEVEL,
    ) -> None:
        super().__init__(logs_dir=logs_dir, file_name=file_name, level=level)
