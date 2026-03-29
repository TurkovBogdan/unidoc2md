"""Single-line input modal: title, prompt, text field, cancel and submit."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.core import locmsg
from src.gui.template.elements import (
    gui_element_button_primary,
    gui_element_button_secondary,
    gui_element_input_text,
)
from src.gui.template.styles import MODAL_FONT_BODY, UI_TYPOGRAPHY, PALETTE

from .base_modal import OverlayModalBase


class InputModal(OverlayModalBase):
    """Prompt for one line: title, prompt, entry, cancel and submit (e.g. Create)."""

    def __init__(
        self,
        parent: tk.Misc,
        submit_text: str | None = None,
        cancel_text: str | None = None,
        **kwargs,
    ) -> None:
        self._default_submit = locmsg("gui.create")
        self._default_cancel = locmsg("gui.cancel")
        self._submit_text = submit_text if submit_text is not None else self._default_submit
        self._cancel_text = cancel_text if cancel_text is not None else self._default_cancel
        self._on_submit = None
        self._title_var: tk.StringVar | None = None
        self._prompt_var: tk.StringVar | None = None
        self._entry_var: tk.StringVar | None = None
        self._input_widget = None
        self._cancel_btn = None
        self._submit_btn = None
        super().__init__(parent, **kwargs)

    def _build_content(self, container: tk.Misc) -> None:
        p = PALETTE
        self._title_var = tk.StringVar(value="")
        self._prompt_var = tk.StringVar(value="")
        self._entry_var = tk.StringVar(value="")
        pady_after = UI_TYPOGRAPHY["header_2"]["pady_after"]
        ttk.Label(
            container,
            textvariable=self._title_var,
            style="ModalHeader2.TLabel",
        ).pack(fill=tk.X, anchor=tk.W, pady=(0, pady_after))
        tk.Label(
            container,
            textvariable=self._prompt_var,
            anchor=tk.W,
            bg=p["bg_elevated"],
            fg=p["text_primary"],
            font=MODAL_FONT_BODY,
        ).pack(fill=tk.X, anchor=tk.W, pady=(0, 4))
        self._input_widget = gui_element_input_text(
            container,
            textvariable=self._entry_var,
            width=36,
        )
        self._input_widget.pack(fill=tk.X, pady=(0, 16))
        self._input_widget.entry.bind("<Return>", lambda _e: self._on_submit_click())
        btn_row = tk.Frame(container, bg=p["bg_elevated"])
        btn_row.pack(fill=tk.X)
        self._cancel_btn = gui_element_button_secondary(btn_row, self._cancel_text, self.hide)
        self._cancel_btn.pack(side=tk.RIGHT, padx=(8, 0))
        self._submit_btn = gui_element_button_primary(
            btn_row, self._submit_text, self._on_submit_click
        )
        self._submit_btn.pack(side=tk.RIGHT)

    def show_input(
        self,
        title: str,
        prompt: str,
        on_submit,
        default: str = "",
        *,
        submit_text: str | None = None,
        cancel_text: str | None = None,
    ) -> None:
        self._title_var.set(title)
        self._prompt_var.set(prompt)
        self._entry_var.set(default)
        self._on_submit = on_submit
        self._submit_btn.configure(
            text=submit_text if submit_text is not None else self._default_submit
        )
        self._cancel_btn.configure(
            text=cancel_text if cancel_text is not None else self._default_cancel
        )
        self.show()
        self.after_idle(lambda: self._input_widget.focus_set())

    def _on_submit_click(self) -> None:
        value = (self._entry_var.get() or "").strip()
        callback = self._on_submit
        self.hide()
        if callback and value:
            callback(value)
