"""GUI runtime config (post-bootstrap). Access via GUIConfigStore."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GUIConfig:
    """GUI parameters set during initialization (bootstrap)."""

    font_family: str | None  # None: use theme fallback


class GUIConfigStore:
    """Single access point for GUI config. Filled in GUIBootstrap._prepare()."""

    _config: GUIConfig | None = None

    @classmethod
    def set(cls, config: GUIConfig) -> None:
        cls._config = config

    @classmethod
    def get(cls) -> GUIConfig:
        if cls._config is None:
            raise RuntimeError("GUI is not initialized (call GUIBootstrap.init first)")
        return cls._config

    @classmethod
    def reset(cls) -> None:
        cls._config = None
