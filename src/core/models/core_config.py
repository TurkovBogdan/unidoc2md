"""The ``[CORE]`` section of ``app.ini``."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CoreConfig:
    """The ``[CORE]`` section of ``app.ini``."""

    debug: bool = False
    log_level: str = field(default="ERROR", metadata={"ini_key": "LEVEL"})
    console_log_level: str = field(default="ERROR", metadata={"ini_key": "CONSOLE_LEVEL"})
    language: str = field(default="", metadata={"ini_key": "LANGUAGE"})
