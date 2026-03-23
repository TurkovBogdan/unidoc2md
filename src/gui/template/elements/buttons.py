"""Кнопки: Primary и Secondary. Стили из template/styles/buttons.py."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def gui_element_button(
    parent: tk.Misc,
    text: str,
    command,
    *,
    style: str = "Primary.TButton",
) -> ttk.Button:
    """Создаёт ttk.Button. Возвращает виджет для pack/grid и при необходимости config(state=...)."""
    return ttk.Button(
        parent, text=text, command=command, style=style, takefocus=False
    )


def gui_element_button_primary(
    parent: tk.Misc,
    text: str,
    command,
) -> ttk.Button:
    """Кнопка основного действия (Primary.TButton)."""
    return gui_element_button(parent, text, command, style="Primary.TButton")


def gui_element_button_secondary(
    parent: tk.Misc,
    text: str,
    command,
) -> ttk.Button:
    """Кнопка вторичного действия (Secondary.TButton)."""
    return gui_element_button(parent, text, command, style="Secondary.TButton")
