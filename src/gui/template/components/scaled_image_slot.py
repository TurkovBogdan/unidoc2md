"""Bitmap icon slot with HiDPI-aware sizing (avoids clipping at logical × scale)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

from src.gui.utils.tk_scaled_image import (
    label_with_photoimage,
    load_scaled_photoimage,
    tk_raster_max_px,
)


class ScaledImageSlot(tk.Frame):
    """
    Container for ``PhotoImage``, aligned with :func:`load_scaled_photoimage`.

    **Logical** size is ``logical_max_pt``. By default the raster is built as
    ``logical_max_pt × tk scaling`` (Retina ~×2). With ``scale_with_display_density=False``,
    raster side is at most ``logical_max_pt`` pixels. Slot side is ``raster_max + gutter``;
    image is centered.
    """

    def __init__(
        self,
        parent: tk.Misc,
        *,
        tk_scaling_ref: tk.Misc,
        logical_max_pt: int = 48,
        gutter: int = 0,
        bg: str | None = None,
        scale_with_display_density: bool = True,
        **kwargs,
    ) -> None:
        kwargs.pop("width", None)
        kwargs.pop("height", None)
        self._tk_scaling_ref = tk_scaling_ref
        self._logical_max_pt = logical_max_pt
        self._gutter = max(0, gutter)
        self._scale_with_display_density = scale_with_display_density
        if scale_with_display_density:
            raster = tk_raster_max_px(tk_scaling_ref, logical_max_pt)
        else:
            raster = max(1, int(logical_max_pt))
        self._raster_max = raster
        side = raster + self._gutter
        super().__init__(parent, width=side, height=side, bg=bg, **kwargs)
        self.pack_propagate(False)
        self._label: tk.Label | None = None

    @property
    def raster_max_px(self) -> int:
        """Max raster side (after ``tk scaling``)."""
        return self._raster_max

    @property
    def logical_max_pt(self) -> int:
        return self._logical_max_pt

    def set_photoimage(self, photo: tk.PhotoImage | None) -> None:
        if self._label is not None:
            self._label.destroy()
            self._label = None
        if photo is None:
            return
        bg = self.cget("bg")
        self._label = label_with_photoimage(self, photo, bg=bg)
        self._label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def load_from_path(self, path: Path) -> None:
        """Load via Pillow / fallback; see :func:`load_scaled_photoimage`."""
        photo = load_scaled_photoimage(
            path,
            self._tk_scaling_ref,
            self._logical_max_pt,
            scale_with_display_density=self._scale_with_display_density,
        )
        self.set_photoimage(photo)


__all__ = ["ScaledImageSlot"]
