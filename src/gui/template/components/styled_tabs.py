"""Стилизованный компонент переключения табов в духе дизайн-системы (PALETTE)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from src.gui.template.styles import PALETTE, UI_FONT_SIZE, UI_TABS
import src.gui.template.styles.theme as _theme  # шрифт читаем в runtime (после gui_setup_theme)


class StyledTabView(ttk.Frame):
    """
    Контейнер с панелью табов и областью контента.
    Цвета и отступы — из UI_TABS (template/styles). Под кнопками — линия 1px цветом активного таба.
    """

    def __init__(
        self,
        parent: tk.Misc,
        tabs: list[tuple[str, str]],
        *,
        initial: str | None = None,
        on_tab_change: Callable[[str], None] | None = None,
        **kwargs,
    ):
        """
        Args:
            parent: Родительский виджет.
            tabs: Список пар (id_таба, подпись), например [("general", "Общие"), ("extract", "Извлечение")].
            initial: Идентификатор таба по умолчанию (если None — первый из списка).
            on_tab_change: Опциональный callback при смене таба: on_tab_change(tab_id).
        """
        super().__init__(parent, **kwargs)
        self._tabs = list(tabs)
        self._on_tab_change = on_tab_change
        self._current: str | None = None
        self._pressed_tab_id: str | None = None  # таб, на котором зажата кнопка мыши
        self._content_frames: dict[str, tk.Misc] = {}
        self._tab_widgets: list[tuple[str, tk.Frame, tk.Label]] = []
        self._bar_frame: tk.Frame | None = None
        self._underline_frame: tk.Frame | None = None

        if not self._tabs:
            return

        ids = [tid for tid, _ in self._tabs]
        if initial is not None and initial in ids:
            self._current = initial
        else:
            self._current = ids[0]

        self._build_tab_bar()
        self._build_content_area()

    def _build_tab_bar(self) -> None:
        p = PALETTE
        t = UI_TABS
        self._bar_frame = tk.Frame(self, bg=p["bg_surface"])
        self._bar_frame.pack(fill=tk.X, pady=(0, t["margin_after_line_px"]))

        inner = tk.Frame(self._bar_frame, bg=p["bg_surface"])
        inner.pack(
            fill=tk.X,
            side=tk.TOP,
            pady=(t["bar_padding_y"], 0),
        )

        for tab_id, label in self._tabs:
            is_selected = tab_id == self._current
            if is_selected:
                bg_tab = t["active"]
                fg_tab = p["text_primary"]
            else:
                bg_tab = t["inactive"]
                fg_tab = p["text_primary"]

            tab_frame = tk.Frame(inner, bg=bg_tab, cursor="hand2")
            tab_frame.pack(side=tk.LEFT, padx=(0, t["gap_px"]))

            lbl = tk.Label(
                tab_frame,
                text=label,
                bg=bg_tab,
                fg=fg_tab,
                font=(_theme.FONT_FAMILY_UI, UI_FONT_SIZE["small"]),
                cursor="hand2",
                padx=t["item_padx"],
                pady=t["item_pady"],
            )
            lbl.pack()

            def _on_enter(_ev: tk.Event, tframe: tk.Frame, tlabel: tk.Label, tid: str) -> None:
                if self._pressed_tab_id is not None:
                    return
                if tid == self._current:
                    tframe.configure(bg=t["hover"])
                    tlabel.configure(bg=t["hover"], fg=p["text_primary"])
                else:
                    tframe.configure(bg=t["inactive_hover"])
                    tlabel.configure(bg=t["inactive_hover"], fg=p["text_primary"])

            def _on_leave(_ev: tk.Event, tid: str) -> None:
                if self._pressed_tab_id is None:
                    self._refresh_tab_bar_style()
                else:
                    self._refresh_tab_bar_style()

            def _on_press(_ev: tk.Event, tframe: tk.Frame, tlabel: tk.Label, tid: str) -> None:
                self._pressed_tab_id = tid
                if tid == self._current:
                    tframe.configure(bg=t["pressed"])
                    tlabel.configure(bg=t["pressed"], fg=p["text_primary"])
                else:
                    tframe.configure(bg=t["inactive_pressed"])
                    tlabel.configure(bg=t["inactive_pressed"], fg=p["text_primary"])

            def _on_release(_ev: tk.Event, tid: str) -> None:
                if self._pressed_tab_id == tid:
                    self._switch_to(tid)
                self._pressed_tab_id = None
                self._refresh_tab_bar_style()

            tab_frame.bind("<ButtonPress-1>", lambda e, tframe=tab_frame, tlabel=lbl, tid=tab_id: _on_press(e, tframe, tlabel, tid))
            tab_frame.bind("<ButtonRelease-1>", lambda e, tid=tab_id: _on_release(e, tid))
            tab_frame.bind("<Enter>", lambda e, tframe=tab_frame, tlabel=lbl, tid=tab_id: _on_enter(e, tframe, tlabel, tid))
            tab_frame.bind("<Leave>", lambda e, tid=tab_id: _on_leave(e, tid))
            lbl.bind("<ButtonPress-1>", lambda e, tframe=tab_frame, tlabel=lbl, tid=tab_id: _on_press(e, tframe, tlabel, tid))
            lbl.bind("<ButtonRelease-1>", lambda e, tid=tab_id: _on_release(e, tid))
            lbl.bind("<Enter>", lambda e, tframe=tab_frame, tlabel=lbl, tid=tab_id: _on_enter(e, tframe, tlabel, tid))
            lbl.bind("<Leave>", lambda e, tid=tab_id: _on_leave(e, tid))

            self._tab_widgets.append((tab_id, tab_frame, lbl))

        # Линия под табами — цвет активного таба
        self._underline_frame = tk.Frame(
            self._bar_frame,
            height=t["underline_height_px"],
            bg=t["underline"],
        )
        self._underline_frame.pack(side=tk.TOP, fill=tk.X)
        self._underline_frame.pack_propagate(False)

    def _build_content_area(self) -> None:
        self._content_holder = ttk.Frame(self)
        self._content_holder.pack(fill=tk.BOTH, expand=True)

    def _switch_to(self, tab_id: str) -> None:
        if tab_id == self._current or tab_id not in self._content_frames:
            return
        self._current = tab_id

        for fid, frame in self._content_frames.items():
            if frame.winfo_ismapped():
                frame.pack_forget()
        self._content_frames[tab_id].pack(fill=tk.BOTH, expand=True)

        self._refresh_tab_bar_style()

        if self._on_tab_change:
            self._on_tab_change(tab_id)

    def _refresh_tab_bar_style(self) -> None:
        p = PALETTE
        t = UI_TABS
        for tab_id, tab_frame, lbl in self._tab_widgets:
            is_selected = tab_id == self._current
            if is_selected:
                bg_tab = t["active"]
                fg_tab = p["text_primary"]
            else:
                bg_tab = t["inactive"]
                fg_tab = p["text_primary"]
            tab_frame.configure(bg=bg_tab)
            lbl.configure(
                bg=bg_tab,
                fg=fg_tab,
                font=(_theme.FONT_FAMILY_UI, UI_FONT_SIZE["small"]),
            )
        if self._underline_frame is not None:
            self._underline_frame.configure(bg=t["underline"])

    def add_tab_content(self, tab_id: str, frame: tk.Misc) -> None:
        """
        Привязывает контентный фрейм к табу.
        Фрейм должен быть создан с parent=view.content_holder.
        Вызывать после создания StyledTabView для каждого таба.
        """
        self._content_frames[tab_id] = frame
        if tab_id == self._current:
            frame.pack(fill=tk.BOTH, expand=True)

    def set_tab(self, tab_id: str) -> None:
        """Переключает на таб по идентификатору (программно)."""
        if tab_id in self._content_frames:
            self._switch_to(tab_id)

    @property
    def content_holder(self) -> ttk.Frame:
        """Фрейм, в который нужно помещать контент табов (для add_tab_content)."""
        return self._content_holder

    def get_current_tab_id(self) -> str | None:
        """Возвращает идентификатор активного таба."""
        return self._current
