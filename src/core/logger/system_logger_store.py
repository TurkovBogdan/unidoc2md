"""Class-based runtime store for the system logger; get() is never None.

Stages (e.g. tagging) may log full LLM system prompts at DEBUG via get().debug(...).
"""

from __future__ import annotations

from src.app_path import AppPath
from src.core.logger.log_levels import DEBUG
from src.core.logger.system_logger import SystemLogger


class SystemLoggerStore:
    """Single access point for the system logger; first ``get()`` creates an instance if needed."""

    _current: SystemLogger | None = None

    @classmethod
    def get(cls) -> SystemLogger:
        """Return the current system logger; if unset, create with default paths and DEBUG level."""
        if cls._current is None:
            paths = AppPath.from_root()
            cls._current = SystemLogger(
                logs_dir=paths.logs_dir,
                file_name="system",
                level=DEBUG,
            )
        return cls._current

    @classmethod
    def set(cls, logger: SystemLogger) -> None:
        """Set the system logger (called from bootstrap)."""
        cls._current = logger

    @classmethod
    def reset(cls) -> None:
        """Clear the current system logger; the next ``get()`` creates a new instance."""
        cls._current = None

    @classmethod
    def set_level(cls, level: int | str) -> None:
        """Apply a log level to the current system logger."""
        cls.get().set_level(level)
