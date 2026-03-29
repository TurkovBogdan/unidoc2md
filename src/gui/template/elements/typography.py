"""Page and section headers shared across screens. Typography from UI_TYPOGRAPHY (template/styles)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.template.styles import UI_INPUT_LABEL_DESCRIPTION, UI_TYPOGRAPHY


def gui_element_page_title(parent: tk.Misc, text: str) -> ttk.Label:
    """Page title (large). Style/spacing from UI_TYPOGRAPHY["page_title"]."""
    t = UI_TYPOGRAPHY["page_title"]
    label = ttk.Label(parent, text=text, style="PageTitle.TLabel")
    label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_page_subtitle(parent: tk.Misc, text: str) -> ttk.Label:
    """Page subtitle. Style/spacing from UI_TYPOGRAPHY["page_subtitle"]."""
    t = UI_TYPOGRAPHY["page_subtitle"]
    label = ttk.Label(parent, text=text, style="PageSubtitle.TLabel")
    label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_header_2(parent: tk.Misc, text: str, *, pack: bool = True) -> ttk.Label:
    """Level-2 section header from UI_TYPOGRAPHY["header_2"]. If pack=True, packs into parent; else return widget for grid."""
    t = UI_TYPOGRAPHY["header_2"]
    label = ttk.Label(parent, text=text, style="Header2.TLabel")
    if pack:
        label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_header_3(parent: tk.Misc, text: str, *, pack: bool = True) -> ttk.Label:
    """Level-3 subsection header from UI_TYPOGRAPHY["header_3"]. If pack=True, packs into parent; else return widget for grid."""
    t = UI_TYPOGRAPHY["header_3"]
    label = ttk.Label(parent, text=text, style="Header3.TLabel")
    if pack:
        label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_header_3_light(parent: tk.Misc, text: str, *, pack: bool = True) -> ttk.Label:
    """Muted level-3 header from UI_TYPOGRAPHY["header_3_light"]. If pack=True, packs into parent; else return widget for grid."""
    t = UI_TYPOGRAPHY["header_3_light"]
    label = ttk.Label(parent, text=text, style="Header3Light.TLabel")
    if pack:
        label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_input_label(
    parent: tk.Misc, text: str, wraplength: int | None = None
) -> ttk.Label:
    """
    Settings field label. Style InputLabel.TLabel from UI_INPUT_LABEL_DESCRIPTION.
    Place in the label column of grid. wraplength (px) enables word wrap (fixes column width).
    """
    label = ttk.Label(parent, text=text, style="InputLabel.TLabel")
    if wraplength is not None:
        label.configure(wraplength=wraplength)
    return label


def gui_element_input_description(
    parent: tk.Misc, text: str, wraplength: int | None = None
) -> ttk.Label | None:
    """
    Settings field hint (muted text under label). Optional: returns None when text == "".
    Style InputLabelDescription.TLabel. wraplength (px) for wrapping (non-stretchy column).
    """
    if not text:
        return None
    label = ttk.Label(parent, text=text, style="InputLabelDescription.TLabel")
    if wraplength is not None:
        label.configure(wraplength=wraplength)
    return label


def gui_element_text_small(
    parent: tk.Misc, text: str, wraplength: int | None = None
) -> ttk.Label:
    """
    Small body text (normal emphasis, not muted).
    Style BodySmall.TLabel (separate from other labels). wraplength (px) for wrapping.
    """
    label = ttk.Label(parent, text=text, style="BodySmall.TLabel")
    if wraplength is not None:
        label.configure(wraplength=wraplength)
    return label
