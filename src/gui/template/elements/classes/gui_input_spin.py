"""Поле выбора числа с кнопками вверх/вниз в стиле системы."""

from __future__ import annotations

import tkinter as tk

from src.gui.template.styles import FONT_FAMILY_UI, UI_FONT_SIZE

from ._common import bind_entry_shortcuts, input_element_typography


class GuiInputSpin(tk.Frame):
    """Поле выбора числа с кнопками вверх/вниз в стиле системы (левая обводка, те же цвета)."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        textvariable: tk.StringVar | None = None,
        from_: int = 0,
        to: int = 100,
        increment: int = 1,
        width: int = 6,
        state: str = "normal",
    ) -> None:
        cfg = input_element_typography()
        super().__init__(parent, bg=cfg["background"], highlightthickness=0, bd=0)
        self._from = from_
        self._to = to
        self._increment = increment
        self._cfg = cfg
        self._variable = textvariable or tk.StringVar(master=self)
        self._state = state

        pad_x, pad_y = cfg["inner_padding"]
        left_bar = tk.Frame(
            self,
            bg=cfg["border"],
            width=cfg["left_border_width"],
            highlightthickness=0,
            bd=0,
        )
        left_bar.pack(side=tk.LEFT, fill=tk.Y)

        body = tk.Frame(self, bg=cfg["background"], highlightthickness=0, bd=0)
        body.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(pad_x, 0), pady=(pad_y, pad_y))

        self._entry = tk.Entry(
            body,
            textvariable=self._variable,
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
        )
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if state != "normal":
            self._entry.configure(state=state)
        bind_entry_shortcuts(self._entry)
        self._entry.bind("<FocusOut>", self._on_focusout, add="+")
        self._entry.bind("<Return>", self._on_focusout, add="+")
        self._entry.bind("<Up>", self._on_arrow_up, add="+")
        self._entry.bind("<Down>", self._on_arrow_down, add="+")
        self._entry.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self._entry.bind("<Button-4>", self._on_mousewheel_linux, add="+")
        self._entry.bind("<Button-5>", self._on_mousewheel_linux, add="+")

        arrow_w, arrow_h = cfg["spin_arrow_size"]
        btn_h = arrow_h + 4
        buttons_frame = tk.Frame(body, bg=cfg["background"], highlightthickness=0, bd=0, width=arrow_w + 8)
        buttons_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(4, pad_x), pady=0)
        buttons_frame.pack_propagate(False)

        self._btn_up = tk.Canvas(
            buttons_frame,
            width=arrow_w + 4,
            height=btn_h,
            bg=cfg["background"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._btn_up.pack(side=tk.TOP, fill=tk.X)
        self._btn_up.create_polygon(
            2, 2 + arrow_h,
            2 + arrow_w // 2, 2,
            2 + arrow_w, 2 + arrow_h,
            fill=cfg["foreground"],
            outline=cfg["foreground"],
        )
        self._btn_up.bind("<Button-1>", lambda _: self._step(1))

        self._btn_down = tk.Canvas(
            buttons_frame,
            width=arrow_w + 4,
            height=btn_h,
            bg=cfg["background"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._btn_down.pack(side=tk.TOP, fill=tk.X)
        self._btn_down.create_polygon(
            2, 2,
            2 + arrow_w // 2, 2 + arrow_h,
            2 + arrow_w, 2,
            fill=cfg["foreground"],
            outline=cfg["foreground"],
        )
        self._btn_down.bind("<Button-1>", lambda _: self._step(-1))

        for w in (self, body, buttons_frame, self._btn_up, self._btn_down):
            w.bind("<MouseWheel>", self._on_mousewheel, add="+")
            w.bind("<Button-4>", self._on_mousewheel_linux, add="+")
            w.bind("<Button-5>", self._on_mousewheel_linux, add="+")

        self._clamp_and_set()

    def _clamp_and_set(self) -> None:
        raw = (self._variable.get() or "").strip()
        if not raw:
            return
        try:
            v = int(raw)
        except (ValueError, TypeError):
            v = self._from
        v = max(self._from, min(self._to, v))
        self._variable.set(str(v))

    def _on_focusout(self, _event: tk.Event | None = None) -> None:
        self._clamp_and_set()

    def _on_arrow_up(self, _event: tk.Event) -> str:
        self._step(1)
        return "break"

    def _on_arrow_down(self, _event: tk.Event) -> str:
        self._step(-1)
        return "break"

    def _on_mousewheel(self, event: tk.Event) -> str:
        delta = getattr(event, "delta", 0)
        if delta > 0:
            self._step(1)
        elif delta < 0:
            self._step(-1)
        return "break"

    def _on_mousewheel_linux(self, event: tk.Event) -> str:
        if event.num == 4:
            self._step(1)
        elif event.num == 5:
            self._step(-1)
        return "break"

    def _step(self, delta: int) -> None:
        if self._state != "normal":
            return
        try:
            raw = self._variable.get() or ""
            v = int(str(raw).strip())
        except (ValueError, TypeError):
            v = self._from
        v = max(self._from, min(self._to, v + delta * self._increment))
        self._variable.set(str(v))

    def get(self) -> str:
        return self._variable.get()

    def focus_set(self) -> None:
        self._entry.focus_set()
