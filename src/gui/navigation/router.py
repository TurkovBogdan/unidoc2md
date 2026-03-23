"""Роутер: переключение слоёв layout и отображаемого экрана по коду."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.navigation.screen_registry import ScreenRegistry

if TYPE_CHECKING:
    from src.gui.gui_layout import GUILayout


class GUIRouter:
    """
    Переключает отображаемый экран: выбор слоя (loader / content / content_console)
    и pack нужного фрейма из реестра, обновление заголовка окна.
    """

    def __init__(self, layout: GUILayout, root: tk.Tk, registry: ScreenRegistry) -> None:
        self._layout = layout
        self._root = root
        self._registry = registry

    def show_screen(self, screen_code: str) -> None:
        """Переключает отображаемый экран по коду и обновляет заголовок окна."""
        if screen_code == "loading":
            self._layout.show_loader()
            frame = self._registry.get("loading")
            if frame is not None:
                frame.pack(fill=tk.BOTH, expand=True)
        else:
            if screen_code == "project_pipeline":
                self._layout.show_content_console()
            else:
                self._layout.show_content()
            for name in self._registry.names():
                if name != "loading":
                    f = self._registry.get(name)
                    if f is not None:
                        f.pack_forget()
            frame = self._registry.get(screen_code)
            if frame is not None:
                frame.pack(fill=tk.BOTH, expand=True)
        self._root.update_idletasks()
        title = self._get_title(screen_code)
        self._root.title(title)

    def _get_title(self, screen_code: str) -> str:
        frame = self._registry.get(screen_code)
        if frame is not None and isinstance(frame, BaseGUIScreen):
            return frame.get_screen_title()
        return "unidoc2md"
