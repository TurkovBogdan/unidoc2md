"""llm_models_registry module config store (initialized at boot)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ModuleConfig:
    """Module params: path to the user registry JSON file."""

    models_store_file: Path


class ModuleConfigStore:
    """Single access point for runtime module configuration."""

    _config: ModuleConfig | None = None

    @classmethod
    def set(cls, config: ModuleConfig) -> None:
        cls._config = config

    @classmethod
    def get(cls) -> ModuleConfig:
        if cls._config is None:
            raise RuntimeError("llm_models_registry module is not initialized")
        return cls._config

    @classmethod
    def reset(cls) -> None:
        cls._config = None
