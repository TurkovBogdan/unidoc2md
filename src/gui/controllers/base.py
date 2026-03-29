"""Base contract for a screen controller (MVP presenter)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from tkinter import ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from src.gui.screens.base_screen import BaseGUIScreen


class BaseScreenController(ABC):
    """
    Screen controller (presenter): coordinates flow and navigation.
    Owns the view (screen), passes callbacks into it; no domain logic here — that lives under ``application/``.
    """

    @property
    @abstractmethod
    def screen_code(self) -> str:
        """Unique screen id for navigation."""
        ...

    @property
    @abstractmethod
    def screen_title(self) -> str:
        """Window title when this screen is shown."""
        ...

    @abstractmethod
    def get_frame(self) -> ttk.Frame | BaseGUIScreen:
        """Root frame/screen widget for the layout."""
        ...

    def on_show(self) -> None:
        """Called when navigating to this screen (refresh data, etc.). Override when needed."""
        pass
