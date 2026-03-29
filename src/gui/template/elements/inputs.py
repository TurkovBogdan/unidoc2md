"""Input factories. Classes live in template/elements/classes/. Scrolled text: template/components.scrollable_text."""

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
    """Text field with themed left accent border."""

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
    """Multiline field, default height 180 px with scrollbar. get()/set(text) for value."""
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
    """Dropdown with themed left accent border."""

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
    """Integer field with up/down arrows (themed left border and colors)."""

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
    """Float field with up/down arrows. Default range 0.0–2.0, step 0.1."""

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
