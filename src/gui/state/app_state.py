"""Контейнер состояния приложения GUI. Передаётся через DI, без глобального singleton."""

from __future__ import annotations

from pathlib import Path


class AppState:
    """Состояние: корень приложения и выбранный проект. Инжектируется через bootstrap/контроллеры."""

    def __init__(self, app_root: Path) -> None:
        self.app_root = app_root
        self.current_project: Path | None = None
