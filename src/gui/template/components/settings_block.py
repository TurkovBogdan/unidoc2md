"""
Settings block: single place for layout and spacing.
All grid(..., pady=..., padx=...) use values from UI_SETTINGS_BLOCK only.
Callers create widgets and call block methods; spacing stays consistent.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from src.gui.template.styles import PALETTE, UI_SETTINGS_BLOCK


def _pady(cfg: dict, top_key: str, bottom_key: str) -> tuple[int, int]:
    return (cfg[top_key], cfg[bottom_key])


class _RowBuilder:
    """Internal row builder: shared spacing for form rows and nested frames."""

    def __init__(self, parent: tk.Misc, cfg: dict) -> None:
        self._parent = parent
        self._cfg = cfg
        self._row = 0

    def _field_row_pady(self) -> tuple[int, int]:
        return _pady(self._cfg, "row_pady_top", "row_pady_bottom")

    def _comment_pady(self) -> tuple[int, int]:
        return _pady(self._cfg, "comment_pady_top", "comment_pady_bottom")

    def _block_sep_pady(self) -> tuple[int, int]:
        return _pady(self._cfg, "block_sep_top", "block_sep_bottom")

    def add_field_row_frame(self) -> ttk.Frame:
        """Add a label|field row frame; call finish_field_row after placing children."""
        c = self._cfg
        frame = ttk.Frame(self._parent)
        frame.grid(row=self._row, column=0, sticky=tk.EW, pady=self._field_row_pady())
        frame.columnconfigure(0, minsize=c["column_label_px"], weight=0)
        frame.columnconfigure(1, minsize=c["column_field_px"], weight=0)
        self._row += 1
        return frame

    def finish_field_row(
        self,
        frame: ttk.Frame,
        label_widget: tk.Widget,
        field_widget: tk.Widget,
    ) -> None:
        """Place label and field in the row frame using cfg spacing."""
        c = self._cfg
        label_widget.grid(row=0, column=0, sticky=tk.W, pady=c["label_pady"])
        field_widget.grid(
            row=0, column=1, sticky=tk.EW,
            padx=c["field_padx"], pady=c["field_pady"],
        )

    def add_comment(self, widget: tk.Widget | None) -> None:
        """Full-width description row."""
        if widget is None:
            return
        widget.grid(
            row=self._row, column=0, sticky=tk.EW,
            pady=self._comment_pady(),
        )
        self._row += 1

    def add_label_row(self, label_widget: tk.Widget) -> None:
        """Single-column label row (above a full-width widget)."""
        label_widget.grid(
            row=self._row, column=0, sticky=tk.W,
            pady=self._field_row_pady(),
        )
        self._row += 1

    def add_full_width_row(self, widget: tk.Widget) -> None:
        """Full-width widget row (e.g. multiline text)."""
        widget.grid(
            row=self._row, column=0, sticky=tk.EW,
            pady=self._field_row_pady(),
        )
        self._row += 1


class SettingsBlock(_RowBuilder):
    """
    Settings block: all grid pady/padx from UI_SETTINGS_BLOCK.
    Callers should not call .grid() with custom padding on these rows.
    """

    def __init__(self, parent: tk.Misc, cfg: dict | None = None) -> None:
        self._cfg = cfg or UI_SETTINGS_BLOCK
        form = tk.Frame(
            parent,
            width=self._cfg["container_width_px"],
            bg=PALETTE["bg_surface"],
        )
        form.pack(anchor=tk.NW, fill=tk.Y)
        form.columnconfigure(0, weight=1)
        super().__init__(form, self._cfg)
        self._form = form

    @property
    def form(self) -> tk.Frame:
        return self._form

    def add_intro_banner(self, widget: tk.Widget) -> int:
        """First banner row; returns row index for show/hide."""
        pady = _pady(self._cfg, "first_row_pady_top", "intro_banner_pady_bottom")
        widget.grid(row=self._row, column=0, sticky=tk.EW, pady=pady)
        r = self._row
        self._row += 1
        return r

    def add_section_banner(self, widget: tk.Widget) -> int:
        """Section start banner (block_sep); returns row index for show/hide."""
        widget.grid(row=self._row, column=0, sticky=tk.EW, pady=self._block_sep_pady())
        r = self._row
        self._row += 1
        return r

    def begin_sub_block(
        self,
        *,
        row_builder_cfg: dict | None = None,
    ) -> tuple[_RowBuilder, ttk.Frame, int]:
        """Nested block; returns (builder, frame, row index for show/hide)."""
        c = self._cfg
        frame = ttk.Frame(self._form)
        frame.grid(row=self._row, column=0, sticky=tk.EW, pady=self._block_sep_pady())
        frame.columnconfigure(0, weight=1)
        r = self._row
        self._row += 1
        inner_cfg = {**c, **(row_builder_cfg or {})}
        return _RowBuilder(frame, inner_cfg), frame, r


def grid_section_banner(widget: tk.Widget, row: int) -> None:
    """Re-show section banner after grid_remove; spacing from UI_SETTINGS_BLOCK."""
    c = UI_SETTINGS_BLOCK
    widget.grid(row=row, column=0, sticky=tk.EW, pady=_pady(c, "block_sep_top", "block_sep_bottom"))


def grid_sub_block(frame: tk.Widget, row: int) -> None:
    """Re-show nested sub-block after grid_remove; spacing from UI_SETTINGS_BLOCK."""
    c = UI_SETTINGS_BLOCK
    frame.grid(row=row, column=0, sticky=tk.EW, pady=_pady(c, "block_sep_top", "block_sep_bottom"))
