"""Инициализация GUI: шрифты, конфиг, создание оформленного root."""

from __future__ import annotations

import sys
from pathlib import Path

import tkinter as tk

from src.core.app_path import project_root
from src.core.logger import SYSTEM_LOGGER

from src.gui.bootstrap.fonts import GuiFontPreparator
from src.gui.gui_config import GUIConfig, GUIConfigStore
from src.gui.template.styles import (
    GUITemplate,
    APP_WINDOW_DEFAULT_HEIGHT,
    APP_WINDOW_DEFAULT_WIDTH,
    APP_WINDOW_MIN_HEIGHT,
    APP_WINDOW_MIN_WIDTH,
    APP_WINDOW_TITLE,
)


class GUIBootstrap:
    """
    1. Инициализирует первичные вещи: шрифты, хранилище конфигурации (GUIConfigStore).
    2. Создаёт и возвращает root с уже применёнными стилями (тема).
    """

    @classmethod
    def _prepare(cls, app_root: Path) -> None:
        """Шрифты и GUIConfigStore. Вызывается из init."""
        font_family = GuiFontPreparator().prepare(app_root)
        GUIConfigStore.set(GUIConfig(font_family=font_family))

    @classmethod
    def _create_root(cls, app_root: Path) -> tk.Tk:
        """Создаёт и настраивает корневое окно Tk. Стили применяются в init."""
        root = tk.Tk()
        root.title(APP_WINDOW_TITLE)
        root.minsize(APP_WINDOW_MIN_WIDTH, APP_WINDOW_MIN_HEIGHT)
        root.geometry(f"{APP_WINDOW_DEFAULT_WIDTH}x{APP_WINDOW_DEFAULT_HEIGHT}")
        root.withdraw()
        return root

    @classmethod
    def set_icon(cls, root: tk.Tk, app_root: Path) -> None:
        """Устанавливает иконку окна из assets/icon.ico (frozen: sys._MEIPASS; dev: app_root или project_root)."""
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
                SYSTEM_LOGGER.debug("Не удалось установить иконку окна: %s", e)

    @classmethod
    def init(cls, app_root: Path) -> tk.Tk:
        """
        Инициализирует окружение (_prepare), создаёт окно, применяет тему, иконку, возвращает root.
        """
        cls._prepare(app_root)
        root = cls._create_root(app_root)
        GUITemplate().apply_theme(root)
        cls.set_icon(root, app_root)
        return root
