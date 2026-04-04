"""
Content layout slots: with and without the pipeline console.

- ``build_content_slot`` — screen area only (all screens except execution).
- ``build_content_console_slot`` — screen area on top + log console at the bottom (execution screen).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.core import locmsg
from src.gui.template.components import scrollable_text
from src.gui.template.styles import (
    PALETTE,
    PROCESSING_BLOCK_HEIGHT_PX,
    GUI_PADDING,
)


def build_content_slot(parent: tk.Misc) -> ContentSlotResult:
    """
    Content slot without console: screen area only.
    ``parent`` is the `GUILayout` container.
    """
    frame = ttk.Frame(parent)
    content_top = ttk.Frame(frame, padding=GUI_PADDING["layout"])
    content_top.pack(fill=tk.BOTH, expand=True)
    return ContentSlotResult(frame=frame, content_top=content_top)


def build_content_console_slot(parent: tk.Misc) -> ContentConsoleSlotResult:
    """
    Content slot with console: screens on top, pipeline log at the bottom.
    ``parent`` is the `GUILayout` container; used for the pipeline execution screen.
    """
    p = PALETTE
    frame = ttk.Frame(parent)

    content_top = ttk.Frame(frame, padding=GUI_PADDING["layout"])
    content_top.pack(fill=tk.BOTH, expand=True)

    bottom_container = tk.Frame(
        frame,
        height=PROCESSING_BLOCK_HEIGHT_PX,
        bg=p["bg_surface"],
    )
    bottom_container.pack_propagate(False)
    bottom_container.pack(side=tk.BOTTOM, fill=tk.X, expand=False)

    header_frame = ttk.Frame(bottom_container)
    header_frame.pack(fill=tk.X, padx=(0, 0), pady=(0, 0))
    console_title_label = ttk.Label(
        header_frame, text=locmsg("project_execution.console_title")
    )
    console_title_label.pack(anchor=tk.W)

    log_container = ttk.Frame(bottom_container)
    log_container.pack(fill=tk.BOTH, expand=True)
    log_text = scrollable_text(log_container, state=tk.DISABLED)

    return ContentConsoleSlotResult(
        frame=frame,
        content_top=content_top,
        log_text=log_text,
        console_title_label=console_title_label,
    )


class ContentSlotResult:
    """Return value of ``build_content_slot``: slot frame and screen area."""

    __slots__ = ("frame", "content_top")

    def __init__(self, frame: ttk.Frame, content_top: ttk.Frame) -> None:
        self.frame = frame
        self.content_top = content_top


class ContentConsoleSlotResult:
    """Return value of ``build_content_console_slot``: slot frame, screen area, log widget."""

    __slots__ = ("frame", "content_top", "log_text", "console_title_label")

    def __init__(
        self,
        frame: ttk.Frame,
        content_top: ttk.Frame,
        log_text: tk.Text,
        console_title_label: ttk.Label,
    ) -> None:
        self.frame = frame
        self.content_top = content_top
        self.log_text = log_text
        self.console_title_label = console_title_label
