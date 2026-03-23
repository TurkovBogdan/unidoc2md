"""Контроллер экрана редактирования одной модели LLM."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.gui.controllers.base import BaseScreenController
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.screens.models_detail import ModelSettingsDetailScreen

if TYPE_CHECKING:
    from src.gui.gui_layout import GUILayout


class ModelSettingsDetailController(BaseScreenController):
    """Координирует экран редактирования модели: навигация назад."""

    def __init__(
        self,
        parent,
        app_root: Path,
        layout: GUILayout,
        *,
        on_back,
    ) -> None:
        self._view = ModelSettingsDetailScreen(
            parent,
            app_root,
            on_back=on_back,
            app_layout=layout,
        )

    @property
    def screen_code(self) -> str:
        return "model_settings_detail"

    @property
    def screen_title(self) -> str:
        return ModelSettingsDetailScreen.SCREEN_TITLE

    def get_frame(self) -> BaseGUIScreen:
        return self._view

    def set_model_key(self, model_key: str) -> None:
        self._view.set_model_key(model_key)
