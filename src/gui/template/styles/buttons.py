"""Button styles: TButton, Primary.TButton, Secondary.TButton, hover cursor."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.template.styles.theme import (
    UI_BUTTONS,
    UI_COLOR_DISABLED,
    UI_COLOR_DISABLED_TEXT,
    UI_COLOR_PRIMARY,
    UI_COLOR_PRIMARY_HOVER,
    UI_COLOR_PRIMARY_PRESSED,
    UI_COLOR_SECONDARY,
    UI_COLOR_SECONDARY_HOVER,
    UI_COLOR_SECONDARY_PRESSED,
    UI_COLOR_SECONDARY_TEXT,
)


def gui_setup_button_styles(
    root: tk.Tk,
    style: ttk.Style,
    palette: dict,
    font: tuple[str | int, ...],
) -> None:
    """
    TButton base (shared + primary colors); Primary.TButton inherits TButton;
    Secondary.TButton uses its own colors. Disabled: UI_COLOR_* from theme.
    Padding and border from UI_BUTTONS, font from theme.
    """
    p = palette
    b = UI_BUTTONS
    _btn_base = {
        "padding": b["padding"],
        "font": font,
        "borderwidth": b["borderwidth"],
        "relief": b["relief"],
        "focuswidth": b["focuswidth"],
    }

    style.configure(
        "TButton",
        background=UI_COLOR_PRIMARY,
        foreground=p["text_primary"],
        focuscolor=UI_COLOR_PRIMARY,
        lightcolor=UI_COLOR_PRIMARY,
        darkcolor=UI_COLOR_PRIMARY,
        bordercolor=UI_COLOR_PRIMARY,
        **_btn_base,
    )
    style.map(
        "TButton",
        background=[
            ("active", UI_COLOR_PRIMARY_HOVER),
            ("pressed", UI_COLOR_PRIMARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
        foreground=[
            ("active", p["text_primary"]),
            ("pressed", p["text_primary"]),
            ("disabled", UI_COLOR_DISABLED_TEXT),
        ],
        relief=[("active", "flat"), ("pressed", "flat")],
        lightcolor=[
            ("active", UI_COLOR_PRIMARY_HOVER),
            ("pressed", UI_COLOR_PRIMARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
        darkcolor=[
            ("active", UI_COLOR_PRIMARY_HOVER),
            ("pressed", UI_COLOR_PRIMARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
        bordercolor=[
            ("active", UI_COLOR_PRIMARY_HOVER),
            ("pressed", UI_COLOR_PRIMARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
    )
    style.configure(
        "Secondary.TButton",
        background=UI_COLOR_SECONDARY,
        foreground=UI_COLOR_SECONDARY_TEXT,
        focuscolor=UI_COLOR_SECONDARY,
        lightcolor=UI_COLOR_SECONDARY,
        darkcolor=UI_COLOR_SECONDARY,
        bordercolor=UI_COLOR_SECONDARY,
        **_btn_base,
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("active", UI_COLOR_SECONDARY_HOVER),
            ("pressed", UI_COLOR_SECONDARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
        foreground=[
            ("active", UI_COLOR_SECONDARY_TEXT),
            ("pressed", UI_COLOR_SECONDARY_TEXT),
            ("disabled", UI_COLOR_DISABLED_TEXT),
        ],
        relief=[("active", "flat"), ("pressed", "flat")],
        lightcolor=[
            ("active", UI_COLOR_SECONDARY_HOVER),
            ("pressed", UI_COLOR_SECONDARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
        darkcolor=[
            ("active", UI_COLOR_SECONDARY_HOVER),
            ("pressed", UI_COLOR_SECONDARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
        bordercolor=[
            ("active", UI_COLOR_SECONDARY_HOVER),
            ("pressed", UI_COLOR_SECONDARY_PRESSED),
            ("disabled", UI_COLOR_DISABLED),
        ],
    )
    # Primary: same as elements; without parent, map may not inherit from TButton (clam default).
    try:
        style.configure("Primary.TButton", parent="TButton")
    except tk.TclError:
        pass
    root.option_add("*TButton*Font", font)

    def _btn_enter(ev: tk.Event) -> None:
        w = ev.widget
        w.configure(cursor=b["cursor"])
        try:
            if w.instate(["!disabled"]):
                w.state(["active"])
        except (tk.TclError, AttributeError):
            pass

    def _btn_leave(ev: tk.Event) -> None:
        w = ev.widget
        w.configure(cursor=b["cursor_leave"])
        try:
            w.state(["!active"])
        except tk.TclError:
            pass

    root.bind_class("TButton", "<Enter>", _btn_enter)
    root.bind_class("TButton", "<Leave>", _btn_leave)

    root.option_add("*TButton*highlightThickness", b["highlight_thickness"])
