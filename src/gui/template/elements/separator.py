"""Horizontal and vertical separators. Settings in UI_SEPARATOR (template/styles)."""

from __future__ import annotations

import tkinter as tk

from src.gui.template.styles import PALETTE, UI_SEPARATOR


def gui_element_separator(parent: tk.Misc) -> tk.Frame:
    """
    Horizontal line. Color, thickness, top/bottom padding from UI_SEPARATOR.
    Place in grid/pack with sticky=tk.EW.
    """
    p = PALETTE
    s = UI_SEPARATOR
    pad = s["padding_horizontal_px"]
    container = tk.Frame(parent, bg=p["bg_surface"], height=s["width_px"] + 2 * pad)
    line = tk.Frame(container, height=s["width_px"], bg=s["color"])
    line.pack(fill=tk.X, pady=(pad, pad))
    container.pack_propagate(False)
    return container


def gui_element_separator_vert(parent: tk.Misc) -> tk.Frame:
    """
    Vertical line. Color, thickness, left/right padding from UI_SEPARATOR.
    Returns outer frame (line inside padding_vertical_px). Use grid with sticky=tk.NS.
    """
    p = PALETTE
    s = UI_SEPARATOR
    pad = s["padding_vertical_px"]
    total_w = s["width_px"] + 2 * pad
    container = tk.Frame(parent, width=total_w, bg=p["bg_surface"])
    container.pack_propagate(False)
    line = tk.Frame(container, width=s["width_px"], bg=s["color"])
    line.pack(fill=tk.Y, padx=(pad, pad), expand=True)
    return container
