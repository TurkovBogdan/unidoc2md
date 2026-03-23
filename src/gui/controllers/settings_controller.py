"""Контроллер экрана настроек приложения."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.gui.controllers.base import BaseScreenController
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.screens.settings import SettingsScreen

if TYPE_CHECKING:
    from src.gui.gui_layout import GUILayout


class SettingsController(BaseScreenController):
    """Координирует экран настроек: только навигация, загрузка/сохранение в экране через adapters."""

    def __init__(
        self,
        parent,
        app_root: Path,
        layout: GUILayout,
        *,
        on_back,
    ) -> None:
        self._view = SettingsScreen(
            parent,
            app_root,
            on_back,
            app_layout=layout,
        )

    @property
    def screen_code(self) -> str:
        return "settings"

    @property
    def screen_title(self) -> str:
        return SettingsScreen.SCREEN_TITLE

    def get_frame(self) -> BaseGUIScreen:
        return self._view
