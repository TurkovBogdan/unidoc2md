"""Текстовое поле на tk.Entry с контролируемой геометрией и цветами."""

from __future__ import annotations

import tkinter as tk

from src.gui.template.styles import FONT_FAMILY_UI, UI_FONT_SIZE

from ._common import bind_entry_shortcuts, input_element_typography


class GuiInputText(tk.Frame):
    """Текстовое поле на tk.Entry с полностью контролируемой геометрией и цветами."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        textvariable: tk.StringVar | None = None,
        width: int = 30,
        state: str = "normal",
        show: str | None = None,
    ) -> None:
        cfg = input_element_typography()
        super().__init__(parent, bg=cfg["background"], highlightthickness=0, bd=0)

        pad_x, pad_y = cfg["inner_padding"]
        left_bar = tk.Frame(
            self,
            bg=cfg["border"],
            width=cfg["left_border_width"],
            highlightthickness=0,
            bd=0,
        )
        left_bar.pack(side=tk.LEFT, fill=tk.Y)
        self.entry = tk.Entry(
            self,
            textvariable=textvariable,
            width=width,
            bg=cfg["background"],
            fg=cfg["foreground"],
            insertbackground=cfg["insertbackground"],
            readonlybackground=cfg["background"],
            disabledbackground=cfg["background"],
            disabledforeground=cfg["foreground"],
            selectbackground=cfg["selection_background"],
            selectforeground=cfg["selection_foreground"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(FONT_FAMILY_UI, UI_FONT_SIZE["small"]),
            show=show,
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(pad_x, pad_x), pady=(pad_y, pad_y))
        if state != "normal":
            self.entry.configure(state=state)
        bind_entry_shortcuts(self.entry)

    def get(self) -> str:
        return self.entry.get()

    def focus_set(self) -> None:
        self.entry.focus_set()
