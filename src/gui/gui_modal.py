"""App modal controller: ``GUIModalsController(modal_layer)``."""

from __future__ import annotations

import tkinter as tk

from src.gui.modals.confirm_modal import ConfirmModal
from src.gui.modals.info_modal import InfoModal
from src.gui.modals.input_modal import InputModal


class GUIModalsController:
    """One shared instance per modal type, bound to the modal overlay layer."""

    def __init__(self, modal_layer: tk.Misc) -> None:
        self._confirm = ConfirmModal(modal_layer)
        self._info = InfoModal(modal_layer)
        self._input = InputModal(modal_layer)

    def show_info(
        self,
        title: str,
        message: str,
        *,
        errors: list[str] | None = None,
    ) -> None:
        self._info.show_info(title, message, errors=errors)

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
        self._confirm.show_confirm(
            title,
            message,
            on_confirm,
            confirm_text=confirm_text,
            cancel_text=cancel_text,
            message_wraplength=message_wraplength,
        )

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
        self._input.show_input(
            title,
            prompt,
            on_submit,
            default,
            submit_text=submit_text,
            cancel_text=cancel_text,
        )
