"""
Apply theme to the root window: ttk styles, fonts, colors.
GUITemplate: instantiate and call apply_theme(root).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import src.gui.template.styles.theme as _theme
from src.gui.template.styles.buttons import gui_setup_button_styles
from src.gui.template.styles.inputs import gui_setup_input_styles


class GUITemplate:
    """Apply unified theme to root Tk (ttk styles, fonts, colors)."""

    def apply_theme(self, root: tk.Tk) -> None:
        """
        Apply the dark green ttk theme.
        Fonts come from GUIConfigStore (filled in GUIBootstrap._prepare).
        """
        from src.gui.gui_config import GUIConfigStore

        cfg = GUIConfigStore.get()
        if cfg.font_family is not None:
            _theme.FONT_FAMILY_UI = _theme.FONT_FAMILY_MONO = cfg.font_family
        _f = _theme.FONT_FAMILY_UI
        _pt = _theme.UI_FONT_SIZE
        _theme.MODAL_FONT_HEADER = (_f, _pt["medium"])
        _theme.MODAL_FONT_BODY = (_f, _pt["small"])

        style = ttk.Style(root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        p = _theme.PALETTE

        # Frames
        style.configure(
            "TFrame",
            background=p["bg_surface"],
            padding=4,
        )
        style.configure(
            "ProjectPanel.TFrame",
            background=p["bg_surface"],
            padding=(0, 4, 0, 4),
        )
        style.configure(
            "TopBar.TFrame",
            background=_theme.GUI_TOPBAR["background"],
        )
        # Labels
        style.configure(
            "TLabel",
            background=p["bg_surface"],
            foreground=p["text_primary"],
            padding=(2, 4),
            font=(_f, _pt["small"]),
        )
        gui_setup_button_styles(root, style, p, (_f, _pt[_theme.UI_BUTTONS["font_size"]]))
        gui_setup_input_styles(root, style, p, (_f, _pt[_theme.UI_INPUTS["font_size"]]))

        # Headers
        style.configure(
            "Header.TLabel",
            background=p["bg_surface"],
            foreground=p["text_primary"],
            font=(_f, _pt["medium"], "normal"),
            padding=(2, 8),
        )
        style.configure(
            "Muted.TLabel",
            background=p["bg_surface"],
            foreground=p["text_muted"],
            font=(_f, _pt["extra_small"]),
        )
        style.configure(
            "Subheader.TLabel",
            background=p["bg_surface"],
            foreground=p["text_primary"],
            font=(_f, _pt["small"]),
        )
        style.configure(
            "BodySmall.TLabel",
            background=p["bg_surface"],
            foreground=p["text_soft"],
            font=(_f, _pt["extra_small"]),
            padding=(0, 0),
        )
        # Field label + description (UI_INPUT_LABEL_DESCRIPTION)
        _ild = _theme.UI_INPUT_LABEL_DESCRIPTION
        style.configure(
            "InputLabel.TLabel",
            background=p["bg_surface"],
            foreground=p["text_primary"],
            font=(_f, _pt[_ild["label_font_size"]]),
            padding=(0, 0),
        )
        _ild_fg = p["text_muted"] if _ild["description_muted"] else p["text_primary"]
        style.configure(
            "InputLabelDescription.TLabel",
            background=p["bg_surface"],
            foreground=_ild_fg,
            font=(_f, _pt[_ild["description_font_size"]]),
            padding=(0, 0),
        )
        # Right panel title (notes / full prompt): no horizontal padding, aligns with body text
        style.configure(
            "RightPanelTitle.TLabel",
            background=p["bg_surface"],
            foreground=p["text_primary"],
            font=(_f, _pt["small"]),
            padding=(0, 4),
        )
        # Page typography from UI_TYPOGRAPHY
        _style_header = (
            ("PageTitle.TLabel", "page_title"),
            ("PageSubtitle.TLabel", "page_subtitle"),
            ("Header2.TLabel", "header_2"),
            ("Header3.TLabel", "header_3"),
            ("Header3Light.TLabel", "header_3_light"),
        )
        for style_name, key in _style_header:
            h = _theme.UI_TYPOGRAPHY[key]
            fg = p["text_muted"] if h["muted"] else p["text_primary"]
            style.configure(
                style_name,
                background=p["bg_surface"],
                foreground=fg,
                font=(_f, _pt[h["font_size"]], "normal"),
                padding=h["padding"],
            )
        # Modal header: like header_2 but elevated background
        _h2 = _theme.UI_TYPOGRAPHY["header_2"]
        style.configure(
            "ModalHeader2.TLabel",
            background=p["bg_elevated"],
            foreground=p["text_primary"],
            font=(_f, _pt[_h2["font_size"]], "normal"),
            padding=_h2["padding"],
        )
        style.configure(
            "TScrollbar",
            background=p["border"],
            troughcolor=p["bg_surface"],
            borderwidth=0,
        )

        style.configure(
            "Treeview",
            background=p["bg_surface"],
            fieldbackground=p["bg_surface"],
            foreground=p["text_primary"],
            bordercolor=p["border"],
            lightcolor=p["border"],
            darkcolor=p["border"],
            rowheight=26,
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", p["select_bg"])],
            foreground=[("selected", p["select_fg"])],
        )
        style.configure(
            "Treeview.Heading",
            background=p["bg_elevated"],
            foreground=p["text_primary"],
            bordercolor=p["border"],
            lightcolor=p["border"],
            darkcolor=p["border"],
            relief="flat",
            font=(_f, _pt["small"]),
            padding=(8, 6),
        )
        style.map(
            "Treeview.Heading",
            background=[
                ("active", _theme.UI_COLOR_PRIMARY_HOVER),
                ("pressed", _theme.UI_COLOR_PRIMARY_PRESSED),
            ],
            foreground=[("active", p["text_primary"]), ("pressed", p["text_primary"])],
        )
        style.configure("Models.Treeview", rowheight=28)

        root.configure(bg=p["bg_main"])


__all__ = ["GUITemplate"]
