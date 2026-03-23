"""Фабрики элементов ввода. Классы инпутов — в template/elements/classes/. Текст со скроллом — template/components.scrollable_text."""

from __future__ import annotations

import tkinter as tk

from src.gui.template.styles import PALETTE

from .classes import GuiInputSelect, GuiInputSpin, GuiInputSpinFloat, GuiInputText, GuiInputTextArea


def gui_element_input_text(
    parent: tk.Misc,
    *,
    textvariable: tk.StringVar | None = None,
    width: int = 30,
    state: str = "normal",
    show: str | None = None,
) -> GuiInputText:
    """Создаёт текстовое поле с жёлтой левой обводкой в 1px."""

    return GuiInputText(
        parent,
        textvariable=textvariable,
        width=width,
        state=state,
        show=show,
    )


def gui_element_input_text_area(
    parent: tk.Misc,
    *,
    height_px: int | None = None,
    state: str = "normal",
) -> GuiInputTextArea:
    """Создаёт многострочное поле высотой 180 px по умолчанию со скроллбаром. get()/set(text) для значения."""
    from .classes.gui_input_text_area import TEXT_AREA_HEIGHT_PX

    return GuiInputTextArea(
        parent,
        height_px=height_px if height_px is not None else TEXT_AREA_HEIGHT_PX,
        state=state,
    )


def gui_element_input_select(
    parent: tk.Misc,
    *,
    variable: tk.StringVar | None = None,
    values: list[str] | tuple[str, ...] = (),
    width: int = 20,
    state: str = "normal",
) -> GuiInputSelect:
    """Создаёт селект с жёлтой левой обводкой в 1px."""

    return GuiInputSelect(
        parent,
        variable=variable,
        values=values,
        width=width,
        state=state,
    )


def gui_element_input_spin(
    parent: tk.Misc,
    *,
    textvariable: tk.StringVar | None = None,
    from_: int = 0,
    to: int = 100,
    increment: int = 1,
    width: int = 6,
    state: str = "normal",
) -> GuiInputSpin:
    """Создаёт поле числа с кнопками вверх/вниз в стиле системы (левая обводка, те же цвета)."""

    return GuiInputSpin(
        parent,
        textvariable=textvariable,
        from_=from_,
        to=to,
        increment=increment,
        width=width,
        state=state,
    )


def gui_element_input_spin_float(
    parent: tk.Misc,
    *,
    textvariable: tk.StringVar | None = None,
    from_: float = 0.0,
    to: float = 2.0,
    increment: float = 0.1,
    width: int = 6,
    decimals: int = 1,
    state: str = "normal",
) -> GuiInputSpinFloat:
    """Создаёт поле дробного числа (float) с кнопками вверх/вниз. По умолчанию 0.0–2.0, шаг 0.1."""

    return GuiInputSpinFloat(
        parent,
        textvariable=textvariable,
        from_=from_,
        to=to,
        increment=increment,
        width=width,
        decimals=decimals,
        state=state,
    )
