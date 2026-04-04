"""
Application-wide layout: switch loader / content / content with console.

Contract: GUILayout builds and toggles slots (loader, content, content_console).
The router decides which slot to show and which screen (frame) to pack there.
Screens only occupy content_top or loader_slot; form spacing uses template.components (SettingsBlock, etc.).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.gui_modal import GUIModalsController
from src.gui.layout.content import build_content_console_slot, build_content_slot
from src.gui.layout.loader import build_loader_slot
from src.gui.template.styles import PALETTE


class GUILayout:
    """
    Root layout: one of loader, content, content_console, etc. Toggle via show(name).
    """

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self.container = ttk.Frame(root)
        self.container.pack(fill=tk.BOTH, expand=True)
        self._slots: dict[str, ttk.Frame] = {}

        # Built-in slots (order: loader, content, content_console)
        loader_frame = build_loader_slot(self.container)
        self._slots["loader"] = loader_frame
        self._loader_slot = loader_frame

        content_result = build_content_slot(self.container)
        self._slots["content"] = content_result.frame
        self.content_top = content_result.content_top

        content_console_result = build_content_console_slot(self.container)
        self._slots["content_console"] = content_console_result.frame
        self.content_console_top = content_console_result.content_top
        self.log_text = content_console_result.log_text
        self.console_title_label = content_console_result.console_title_label

        # Modal layer above current layout (color from styles.PALETTE["modal_overlay"])
        self._modal_layer = tk.Frame(self.container, bg=PALETTE["modal_overlay"])
        self._modal_layer._is_app_modal_layer = True  # for OverlayModalBase.show/hide
        self._modals_registry = GUIModalsController(self._modal_layer)

    @property
    def modals(self) -> GUIModalsController:
        """Modal controller: show_info, show_confirm, show_input."""
        return self._modals_registry

    @property
    def loader_slot(self) -> ttk.Frame:
        """Full-screen loader slot."""
        return self._loader_slot

    def add_slot(self, name: str) -> ttk.Frame:
        """Add another top-level slot. Returns the frame to fill."""
        if name in self._slots:
            return self._slots[name]
        frame = ttk.Frame(self.container)
        self._slots[name] = frame
        return frame

    def show(self, name: str) -> None:
        """Show a slot by name (loader, content, content_console, or add_slot name)."""
        for slot in self._slots.values():
            slot.pack_forget()
        if name in self._slots:
            self._slots[name].pack(fill=tk.BOTH, expand=True)

    def show_loader(self) -> None:
        """Show the loader layer."""
        self.show("loader")

    def show_content(self) -> None:
        """Content without console (home, project, settings, …)."""
        self.show("content")

    def show_content_console(self) -> None:
        """Content with bottom console (pipeline execution screen)."""
        self.show("content_console")


def create_gui_layout(root: tk.Tk) -> GUILayout:
    """Create layout; container is packed into root."""
    return GUILayout(root)
