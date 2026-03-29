"""Custom dropdown without native Menu (avoids Windows menu quirks)."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
import time

from src.gui.template.styles import FONT_FAMILY_UI, UI_FONT_SIZE

from ._common import input_element_typography


class GuiInputSelect(tk.Frame):
    """Custom dropdown without native Menu (avoids Windows menu quirks)."""

    def __init__(
        self,
        parent: tk.Misc,
        *,
        variable: tk.StringVar | None = None,
        values: list[str] | tuple[str, ...] = (),
        width: int = 20,
        state: str = "normal",
    ) -> None:
        cfg = input_element_typography()
        super().__init__(parent, bg=cfg["background"], highlightthickness=0, bd=0)

        self.variable = variable or tk.StringVar(master=self)
        self._values = list(values)
        self._cfg = cfg
        self._state = state
        self._popup: tk.Toplevel | None = None
        self._listbox: tk.Listbox | None = None
        self._hover_index: int | None = None
        self._ignore_clicks_until = 0.0
        if self._values and not self.variable.get():
            self.variable.set(self._values[0])

        pad_x, pad_y = cfg["inner_padding"]
        left_bar = tk.Frame(
            self,
            bg=cfg["border"],
            width=cfg["left_border_width"],
            highlightthickness=0,
            bd=0,
        )
        left_bar.pack(side=tk.LEFT, fill=tk.Y)

        self._body = tk.Frame(
            self,
            bg=cfg["background"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
            takefocus=1,
        )
        self._body.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(pad_x, pad_x), pady=(pad_y, pad_y))

        self._value_label = tk.Label(
            self._body,
            text=self.variable.get(),
            width=width,
            anchor="w",
            bg=cfg["background"],
            fg=cfg["foreground"],
            font=(FONT_FAMILY_UI, UI_FONT_SIZE["small"]),
            highlightthickness=0,
            bd=0,
        )
        self._value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._arrow = tk.Canvas(
            self._body,
            width=cfg["select_arrow_width"] + 4,
            height=cfg["select_arrow_height"] + 4,
            bg=cfg["background"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._arrow.pack(side=tk.RIGHT, padx=(8, 0))
        self._draw_arrow()

        self.variable.trace_add("write", self._on_value_change)

        for widget in (self, left_bar, self._body, self._value_label, self._arrow):
            widget.bind("<Button-1>", self._toggle_popup, add="+")
            widget.bind("<Down>", self._open_popup_from_keyboard, add="+")
            widget.bind("<Up>", self._open_popup_from_keyboard, add="+")
            widget.bind("<Return>", self._open_popup_from_keyboard, add="+")
            widget.bind("<space>", self._open_popup_from_keyboard, add="+")
            widget.bind("<MouseWheel>", self._on_wheel_select, add="+")
            widget.bind("<Button-4>", self._on_wheel_select_linux, add="+")
            widget.bind("<Button-5>", self._on_wheel_select_linux, add="+")

        if state != "normal":
            self._value_label.configure(cursor="")
            self._arrow.configure(cursor="")
            self._body.configure(cursor="")

    def get(self) -> str:
        return self.variable.get()

    def _draw_arrow(self) -> None:
        cfg = self._cfg
        w = cfg["select_arrow_width"]
        h = cfg["select_arrow_height"]
        self._arrow.delete("all")
        self._arrow.create_polygon(
            2,
            2,
            2 + w,
            2,
            2 + (w // 2),
            2 + h,
            fill=cfg["foreground"],
            outline=cfg["foreground"],
        )

    def _on_value_change(self, *_args) -> None:
        self._value_label.configure(text=self.variable.get())

    def _toggle_popup(self, _event: tk.Event | None = None) -> str | None:
        if self._state != "normal":
            return "break"
        if time.monotonic() < self._ignore_clicks_until:
            return "break"
        if self._popup is not None and self._popup.winfo_exists():
            self._close_popup()
            return "break"
        self._open_popup()
        return "break"

    def _open_popup_from_keyboard(self, _event: tk.Event | None = None) -> str:
        if self._state != "normal":
            return "break"
        if self._popup is None or not self._popup.winfo_exists():
            self._open_popup()
        elif self._listbox is not None:
            self._listbox.focus_set()
        return "break"

    def _open_popup(self) -> None:
        if not self._values:
            return
        cfg = self._cfg
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = self.winfo_width()

        self._popup = tk.Toplevel(self)
        self._popup.overrideredirect(True)
        self._popup.configure(bg=cfg["border"])
        self._popup.geometry(f"+{x}+{y}")

        popup_border = cfg["select_popup_borderwidth"]
        pad_left_px = cfg["select_popup_item_padding_left"]
        height = min(len(self._values), cfg["select_popup_max_rows"])
        # Left padding via text prefix so selection highlight spans full row
        listbox_font = tkfont.Font(family=FONT_FAMILY_UI, size=UI_FONT_SIZE["small"])
        n = 0
        while listbox_font.measure(" " * (n + 1)) <= pad_left_px and n < 200:
            n += 1
        item_prefix = " " * n

        self._listbox = tk.Listbox(
            self._popup,
            width=max(1, self._value_label.cget("width")),
            height=height,
            bg=cfg["background"],
            fg=cfg["foreground"],
            selectbackground=cfg["selection_background"],
            selectforeground=cfg["selection_foreground"],
            activestyle="none",
            relief="flat",
            bd=0,
            highlightthickness=0,
            exportselection=False,
            font=listbox_font,
            cursor="hand2",
        )
        self._listbox.pack(fill=tk.BOTH, expand=True, padx=popup_border, pady=popup_border)

        for value in self._values:
            self._listbox.insert(tk.END, item_prefix + value)

        if self.variable.get() in self._values:
            current_index = self._values.index(self.variable.get())
            self._listbox.selection_set(current_index)
            self._listbox.activate(current_index)
            self._listbox.see(current_index)
            self._hover_index = current_index

        self._listbox.bind("<ButtonRelease-1>", self._select_from_popup, add="+")
        self._listbox.bind("<Return>", self._select_from_popup, add="+")
        self._listbox.bind("<Escape>", self._close_popup_event, add="+")
        self._listbox.bind("<Motion>", self._on_listbox_motion, add="+")
        self._listbox.bind("<Leave>", self._on_listbox_leave, add="+")
        self._listbox.bind("<Up>", self._on_arrow_up, add="+")
        self._listbox.bind("<Down>", self._on_arrow_down, add="+")
        self._listbox.bind("<MouseWheel>", self._on_wheel_select, add="+")
        self._listbox.bind("<Button-4>", self._on_wheel_select_linux, add="+")
        self._listbox.bind("<Button-5>", self._on_wheel_select_linux, add="+")
        self._popup.bind("<FocusOut>", lambda _e: self._close_popup(), add="+")
        self._popup.update_idletasks()
        popup_height = self._listbox.winfo_reqheight() + (popup_border * 2)
        self._popup.geometry(f"{width}x{popup_height}+{x}+{y}")
        self._listbox.focus_set()

    def _select_from_popup(self, _event: tk.Event | None = None) -> str:
        if self._listbox is None:
            return "break"
        selection = self._listbox.curselection()
        if selection:
            self.variable.set(self._values[selection[0]])
        # Short debounce: ignore echo click right after closing the popup.
        self._ignore_clicks_until = time.monotonic() + 0.12
        self._close_popup()
        return "break"

    def _close_popup(self) -> None:
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None
        self._listbox = None
        self._hover_index = None
        if self._state == "normal":
            self._body.focus_set()

    def _close_popup_event(self, _event: tk.Event | None = None) -> str:
        self._close_popup()
        return "break"

    def _set_listbox_index(self, index: int) -> None:
        if self._listbox is None or not self._values:
            return
        index = max(0, min(index, len(self._values) - 1))
        self._listbox.selection_clear(0, tk.END)
        self._listbox.selection_set(index)
        self._listbox.activate(index)
        self._listbox.see(index)
        self._hover_index = index

    def _selected_or_current_index(self) -> int:
        if not self._values:
            return 0
        if self._listbox is not None:
            selection = self._listbox.curselection()
            if selection:
                return selection[0]
        if self.variable.get() in self._values:
            return self._values.index(self.variable.get())
        return 0

    def _on_arrow_up(self, _event: tk.Event) -> str:
        self._set_listbox_index(self._selected_or_current_index() - 1)
        return "break"

    def _on_arrow_down(self, _event: tk.Event) -> str:
        self._set_listbox_index(self._selected_or_current_index() + 1)
        return "break"

    def _on_wheel_select(self, event: tk.Event) -> str:
        """Wheel changes selection only when popup is open; otherwise let page scroll."""
        if self._popup is None or not self._popup.winfo_exists():
            return
        delta = getattr(event, "delta", 0)
        if delta > 0:
            self._wheel_step(-1)
        elif delta < 0:
            self._wheel_step(1)
        return "break"

    def _on_wheel_select_linux(self, event: tk.Event) -> str:
        """Same as _on_wheel_select for Linux (Button-4/5)."""
        if self._popup is None or not self._popup.winfo_exists():
            return
        if event.num == 4:
            self._wheel_step(-1)
        elif event.num == 5:
            self._wheel_step(1)
        return "break"

    def _wheel_step(self, step: int) -> None:
        """Move selection by step: -1 previous, +1 next."""
        if self._state != "normal" or not self._values:
            return
        current = self.variable.get()
        idx = self._values.index(current) if current in self._values else 0
        new_idx = max(0, min(len(self._values) - 1, idx + step))
        if new_idx != idx:
            self.variable.set(self._values[new_idx])
            if self._listbox is not None and self._listbox.winfo_exists():
                self._set_listbox_index(new_idx)

    def _on_listbox_motion(self, event: tk.Event) -> str:
        if self._listbox is None:
            return "break"
        index = self._listbox.nearest(event.y)
        if index != self._hover_index:
            self._set_listbox_index(index)
        return "break"

    def _on_listbox_leave(self, _event: tk.Event) -> str:
        if self._listbox is None:
            return "break"
        if self.variable.get() in self._values:
            current_index = self._values.index(self.variable.get())
            self._set_listbox_index(current_index)
        else:
            self._set_listbox_index(self._selected_or_current_index())
        return "break"

    def set_values(self, values: list[str] | tuple[str, ...]) -> None:
        self._values = list(values)
        if self._values and self.variable.get() not in self._values:
            self.variable.set(self._values[0])
        elif not self._values:
            self.variable.set("")

    def set_field_state(self, state: str) -> None:
        """normal: dropdown works; disabled: blocked like other form fields."""
        self._state = state if state in ("normal", "disabled") else "normal"
        self._close_popup()
        if self._state == "normal":
            self._value_label.configure(cursor="")
            self._arrow.configure(cursor="hand2")
            self._body.configure(cursor="hand2")
        else:
            self._value_label.configure(cursor="")
            self._arrow.configure(cursor="")
            self._body.configure(cursor="")

    def focus_set(self) -> None:
        self._body.focus_set()
