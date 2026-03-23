"""Конфигурация GUI (параметры после boot). Доступ через GUIConfigStore."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GUIConfig:
    """Параметры GUI, заданные при инициализации (bootstrap)."""

    font_family: str | None  # None — использовать fallback из темы


class GUIConfigStore:
    """Единая точка доступа к конфигурации GUI. Заполняется в GUIBootstrap._prepare()."""

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
