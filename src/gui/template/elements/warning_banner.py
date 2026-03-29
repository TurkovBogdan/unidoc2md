"""Warning banner: text with a vertical accent line on the left."""

from __future__ import annotations

import tkinter as tk

from src.gui.template.styles import FONT_FAMILY_UI, PALETTE, UI_COLOR_PRIMARY, UI_FONT_SIZE

WARNING_BAR_WIDTH_PX = 4
WARNING_PADDING_PX = (10, 8)


def gui_element_warning_banner(parent: tk.Misc, text: str) -> tk.Frame:
    """
    Warning strip: vertical primary-colored bar on the left, text on the right.
    Returns container for grid/pack.
    """
    p = PALETTE
    container = tk.Frame(parent, bg=p["bg_surface"])
    bar = tk.Frame(container, width=WARNING_BAR_WIDTH_PX, bg=UI_COLOR_PRIMARY)
    bar.pack(side=tk.LEFT, fill=tk.Y)
    bar.pack_propagate(False)
    label = tk.Label(
        container,
        text=text,
        bg=p["bg_surface"],
        fg=p["text_muted"],
        font=(FONT_FAMILY_UI, UI_FONT_SIZE["extra_small"]),
        anchor=tk.W,
        justify=tk.LEFT,
        padx=WARNING_PADDING_PX[0],
        pady=WARNING_PADDING_PX[1],
    )
    label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    return container
