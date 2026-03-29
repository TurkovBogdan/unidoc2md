"""Base class for a full-frame application screen."""

from __future__ import annotations

from pathlib import Path
from tkinter import ttk
from typing import TYPE_CHECKING, Any

from src.core import locmsg

if TYPE_CHECKING:
    from src.gui.gui_layout import GUILayout


class BaseGUIScreen(ttk.Frame):
    """
    Base class for a screen that fills the app content area.

    A screen is an independent UI layer switched by navigation. Subclasses set
    SCREEN_CODE and optionally SCREEN_TITLE, may override get_screen_title(), and
    implement _build_ui().
    """

    SCREEN_CODE: str = ""
    SCREEN_TITLE: str = ""

    def __init__(
        self,
        parent: ttk.Frame,
        *,
        app_root: Path | None = None,
        app_layout: GUILayout | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self._app_root = app_root
        self._app_layout = app_layout

    @classmethod
    def get_screen_code(cls) -> str:
        """Stable screen id for navigation and routing."""
        return cls.SCREEN_CODE

    def get_screen_title(self) -> str:
        """Window title while this screen is visible."""
        return self.SCREEN_TITLE or locmsg("app.title")

    def _build_ui(self) -> None:
        """
        Builds the screen UI; override in subclasses.
        Called from __init__ after the base class is initialized.
        """
        pass
