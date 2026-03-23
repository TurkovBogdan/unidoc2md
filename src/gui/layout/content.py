"""
Слоты layout «Контент»: без консоли и с консолью.

- build_content_slot — только область экранов (все экраны кроме выполнения).
- build_content_console_slot — область экранов сверху + консоль «Обработка данных» снизу (экран выполнения).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.template.components import scrollable_text
from src.gui.template.styles import (
    PALETTE,
    PROCESSING_BLOCK_HEIGHT_PX,
    GUI_PADDING,
)


def build_content_slot(parent: tk.Misc) -> ContentSlotResult:
    """
    Создаёт слот контента без консоли: только область для экранов.
    Родитель — container GUILayout.
    """
    frame = ttk.Frame(parent)
    content_top = ttk.Frame(frame, padding=GUI_PADDING["layout"])
    content_top.pack(fill=tk.BOTH, expand=True)
    return ContentSlotResult(frame=frame, content_top=content_top)


def build_content_console_slot(parent: tk.Misc) -> ContentConsoleSlotResult:
    """
    Создаёт слот контента с консолью: область экранов сверху, консоль «Обработка данных» снизу.
    Родитель — container GUILayout. Используется для экрана выполнения pipeline.
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
    ttk.Label(header_frame, text="Обработка данных").pack(anchor=tk.W)

    log_container = ttk.Frame(bottom_container)
    log_container.pack(fill=tk.BOTH, expand=True)
    log_text = scrollable_text(log_container, state=tk.DISABLED)

    return ContentConsoleSlotResult(
        frame=frame,
        content_top=content_top,
        log_text=log_text,
    )


class ContentSlotResult:
    """Результат build_content_slot: фрейм слота, область экранов."""

    __slots__ = ("frame", "content_top")

    def __init__(self, frame: ttk.Frame, content_top: ttk.Frame) -> None:
        self.frame = frame
        self.content_top = content_top


class ContentConsoleSlotResult:
    """Результат build_content_console_slot: фрейм слота, область экранов, виджет лога."""

    __slots__ = ("frame", "content_top", "log_text")

    def __init__(
        self,
        frame: ttk.Frame,
        content_top: ttk.Frame,
        log_text: tk.Text,
    ) -> None:
        self.frame = frame
        self.content_top = content_top
        self.log_text = log_text
