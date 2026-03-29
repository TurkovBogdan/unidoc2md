"""Multiline text with vertical scrollbar and fixed height."""

from __future__ import annotations

import tkinter as tk

from src.gui.template.styles import FONT_FAMILY_UI, PALETTE, UI_FONT_SIZE

from src.gui.template.components.custom_scrollbar import CustomScrollbar

from ._common import bind_text_shortcuts, input_element_typography

# Default text area height (px)
TEXT_AREA_HEIGHT_PX = 180


class GuiInputTextArea(tk.Frame):
    """
    Multiline input: tk.Text + vertical scrollbar.
    Height in pixels (default 180 px).
    Use get() / set(text) for content.
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        height_px: int = TEXT_AREA_HEIGHT_PX,
        state: str = "normal",
    ) -> None:
        cfg = input_element_typography()
        super().__init__(parent, bg=cfg["background"], highlightthickness=0, bd=0, height=height_px)
        self.pack_propagate(False)

        self._text = tk.Text(
            self,
            wrap=tk.WORD,
            state=state,
            font=(FONT_FAMILY_UI, UI_FONT_SIZE["small"]),
            bg=PALETTE["bg_elevated"],
            fg=PALETTE["text_primary"],
            insertbackground=PALETTE["text_primary"],
            selectbackground=PALETTE["select_bg"],
            selectforeground=PALETTE["select_fg"],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
        )
        self._scrollbar = CustomScrollbar(self, command=self._text.yview)
        self._text.configure(yscrollcommand=self._scrollbar.set)
        bind_text_shortcuts(self._text)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def get(self) -> str:
        return self._text.get("1.0", tk.END).rstrip("\n")

    def set(self, value: str) -> None:
        self._text.delete("1.0", tk.END)
        if value:
            self._text.insert(tk.END, value)

    def focus_set(self) -> None:
        self._text.focus_set()
