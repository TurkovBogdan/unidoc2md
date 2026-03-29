"""Controller for editing a single LLM model."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.gui.controllers.base import BaseScreenController
from src.gui.screens.base_screen import BaseGUIScreen

if TYPE_CHECKING:
    from src.gui.gui_layout import GUILayout

from src.gui.screens.models_detail import ModelSettingsDetailScreen


class ModelSettingsDetailController(BaseScreenController):
    """Coordinates the model detail screen: back navigation."""

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
        return self._view.get_screen_title()

    def get_frame(self) -> BaseGUIScreen:
        return self._view

    def set_model_key(self, model_key: str) -> None:
        self._view.set_model_key(model_key)
