"""GUI initialization: fonts, config store, styled root window."""

from __future__ import annotations

import sys
from pathlib import Path

import tkinter as tk

from src.core.app_path import project_root
from src.core.logger import SYSTEM_LOGGER

from src.gui.bootstrap.fonts import GuiFontPreparator
from src.gui.gui_config import GUIConfig, GUIConfigStore
from src.core import locmsg
from src.gui.template.styles import (
    GUITemplate,
    APP_WINDOW_DEFAULT_HEIGHT,
    APP_WINDOW_DEFAULT_WIDTH,
    APP_WINDOW_MIN_HEIGHT,
    APP_WINDOW_MIN_WIDTH,
)


class GUIBootstrap:
    """
    1. Prepare fonts and ``GUIConfigStore``.
    2. Create and return a ``Tk`` root with the template theme applied.
    """

    @classmethod
    def _prepare(cls, app_root: Path) -> None:
        """Fonts and ``GUIConfigStore``; called from ``init``."""
        font_family = GuiFontPreparator().prepare(app_root)
        GUIConfigStore.set(GUIConfig(font_family=font_family))

    @classmethod
    def _create_root(cls, app_root: Path) -> tk.Tk:
        """Create and configure the root ``Tk`` window. Theme is applied in ``init``."""
        root = tk.Tk()
        root.title(locmsg("gui.window_title"))
        root.minsize(APP_WINDOW_MIN_WIDTH, APP_WINDOW_MIN_HEIGHT)
        root.geometry(f"{APP_WINDOW_DEFAULT_WIDTH}x{APP_WINDOW_DEFAULT_HEIGHT}")
        root.withdraw()
        return root

    @classmethod
    def set_icon(cls, root: tk.Tk, app_root: Path) -> None:
        """Set window icon from ``assets/icon.ico`` (frozen: ``sys._MEIPASS``; dev: ``app_root`` or project root)."""
        if getattr(sys, "frozen", False):
            _icon = Path(sys._MEIPASS) / "assets" / "icon.ico"
        else:
            _icon = app_root / "assets" / "icon.ico"
            if not _icon.is_file():
                _icon = project_root() / "assets" / "icon.ico"
        if _icon.is_file():
            try:
                root.iconbitmap(_icon)
            except tk.TclError as e:
                SYSTEM_LOGGER.debug("Failed to set window icon: %s", e)

    @classmethod
    def init(cls, app_root: Path) -> tk.Tk:
        """Run ``_prepare``, create the window, apply theme and icon, return ``root``."""
        cls._prepare(app_root)
        root = cls._create_root(app_root)
        GUITemplate().apply_theme(root)
        cls.set_icon(root, app_root)
        return root
