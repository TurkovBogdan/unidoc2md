"""Controller for the LLM model list screen."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.gui.controllers.base import BaseScreenController
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.screens.models import ModelSettingsScreen

if TYPE_CHECKING:
    from src.gui.gui_layout import GUILayout


class ModelSettingsController(BaseScreenController):
    """Coordinates the model list screen: navigation and opening the detail view."""

    def __init__(
        self,
        parent,
        app_root: Path,
        layout: GUILayout,
        *,
        on_back,
        on_edit_model,
    ) -> None:
        self._view = ModelSettingsScreen(
            parent,
            app_root,
            on_back=on_back,
            on_edit_model=on_edit_model,
            app_layout=layout,
        )

    @property
    def screen_code(self) -> str:
        return "model_settings"

    @property
    def screen_title(self) -> str:
        return self._view.get_screen_title()

    def get_frame(self) -> BaseGUIScreen:
        return self._view
