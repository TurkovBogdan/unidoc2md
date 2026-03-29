"""Class-based runtime store and facade for AppConfig."""

from __future__ import annotations

from pathlib import Path

from src.app_config import AppConfig


class AppConfigStore:
    """Single class-based access point for the runtime config and app.ini."""

    _current: AppConfig | None = None
    _runtime_root: Path | None = None

    @classmethod
    def get(cls) -> AppConfig:
        """Return the current active config; if unset, ``AppConfig.default()``."""
        if cls._current is None:
            return AppConfig.default()
        return cls._current

    @classmethod
    def set(cls, config: AppConfig | None) -> None:
        """Set the current active config; ``None`` is equivalent to reset."""
        cls._current = config

    @classmethod
    def reset(cls) -> None:
        """Clear the current config; after ``reset()``, ``get()`` returns ``AppConfig.default()``."""
        cls._current = None
        cls._runtime_root = None

    @classmethod
    def load_or_create(cls, root: Path | None = None) -> AppConfig:
        """Load or create ``app.ini``, update the runtime store, and return ``AppConfig``."""
        from .app_config_builder import load_or_create as _builder_load_or_create
        from .app_path import resolve_runtime_root

        resolved = Path(root).resolve() if root is not None else resolve_runtime_root().resolve()
        config = _builder_load_or_create(resolved)
        cls._runtime_root = resolved
        cls.set(config)
        return config

    @classmethod
    def save(cls, config: AppConfig, root: Path | None = None) -> None:
        """
        Write the full ``AppConfig`` to ``app.ini`` (same root as ``load_or_create``) and
        replace the in-memory object so subsequent ``get()`` returns this config.
        """
        from .app_config_builder import save_config as _builder_save_config
        from .app_path import resolve_runtime_root

        if root is not None:
            resolved = Path(root).resolve()
        elif cls._runtime_root is not None:
            resolved = cls._runtime_root
        else:
            resolved = resolve_runtime_root().resolve()
        _builder_save_config(config, resolved)
        cls._runtime_root = resolved
        cls.set(config)
