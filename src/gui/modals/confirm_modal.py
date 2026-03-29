"""Confirmation modal: title, message, cancel and primary action buttons."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.core import locmsg
from src.gui.template.styles import MODAL_FONT_BODY, MODAL_MESSAGE_WRAP, UI_TYPOGRAPHY, PALETTE

from .base_modal import OverlayModalBase


class ConfirmModal(OverlayModalBase):
    """Confirm an action: title, message, cancel and confirm (e.g. Delete)."""

    def __init__(
        self,
        parent: tk.Misc,
        confirm_text: str | None = None,
        cancel_text: str | None = None,
        **kwargs,
    ) -> None:
        self._default_confirm = locmsg("gui.ok")
        self._default_cancel = locmsg("gui.cancel")
        self._confirm_text = confirm_text if confirm_text is not None else self._default_confirm
        self._cancel_text = cancel_text if cancel_text is not None else self._default_cancel
        self._on_confirm = None
        self._title_var: tk.StringVar | None = None
        self._message_var: tk.StringVar | None = None
        super().__init__(parent, **kwargs)

    def _build_content(self, container: tk.Misc) -> None:
        p = PALETTE
        self._title_var = tk.StringVar(value=locmsg("gui.modal.confirm_title"))
        self._message_var = tk.StringVar(value="")
        pady_after = UI_TYPOGRAPHY["header_2"]["pady_after"]
        ttk.Label(
            container,
            textvariable=self._title_var,
            style="ModalHeader2.TLabel",
        ).pack(fill=tk.X, anchor=tk.W, pady=(0, pady_after))
        self._message_lbl = tk.Label(
            container,
            textvariable=self._message_var,
            wraplength=MODAL_MESSAGE_WRAP,
            justify=tk.LEFT,
            anchor=tk.W,
            bg=p["bg_elevated"],
            fg=p["text_primary"],
            font=MODAL_FONT_BODY,
        )
        self._message_lbl.pack(fill=tk.X, anchor=tk.W, pady=(0, 16))
        btn_row = tk.Frame(container, bg=p["bg_elevated"])
        btn_row.pack(fill=tk.X)
        self._cancel_btn = ttk.Button(
            btn_row,
            text=self._cancel_text,
            command=self.hide,
            style="Secondary.TButton",
            takefocus=False,
        )
        self._cancel_btn.pack(side=tk.RIGHT, padx=(8, 0))
        self._confirm_btn = ttk.Button(
            btn_row,
            text=self._confirm_text,
            command=self._on_confirm_click,
            style="Primary.TButton",
            takefocus=False,
        )
        self._confirm_btn.pack(side=tk.RIGHT)

    def show_confirm(
        self,
        title: str,
        message: str,
        on_confirm,
        *,
        confirm_text: str | None = None,
        cancel_text: str | None = None,
        message_wraplength: int | None = None,
    ) -> None:
        self._title_var.set(title)
        self._message_var.set(message)
        self._on_confirm = on_confirm
        wrap = MODAL_MESSAGE_WRAP if message_wraplength is None else message_wraplength
        self._message_lbl.configure(wraplength=wrap)
        self._confirm_btn.configure(
            text=confirm_text if confirm_text is not None else self._default_confirm
        )
        self._cancel_btn.configure(
            text=cancel_text if cancel_text is not None else self._default_cancel
        )
        self.show()

    def _on_confirm_click(self) -> None:
        callback = self._on_confirm
        self.hide()
        if callback:
            callback()
