"""Load bitmaps into tk.PhotoImage with tk scaling (HiDPI / Retina)."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

from src.core.app_path import project_root


def tk_raster_max_px(tk_widget: tk.Misc, logical_pt: int) -> int:
    """
    Max image side in pixels for a logical size in pt.

    `tk scaling` is pixels per typographic point; on Retina / HiDPI it is usually >1.
    Layout stays `logical_pt` in Tk units; the raster is denser for the display.
    """
    if logical_pt <= 0:
        logical_pt = 1
    try:
        spp = float(tk_widget.tk.call("tk", "scaling", "-displayof", tk_widget))
    except tk.TclError:
        spp = 1.0
    if spp <= 0:
        spp = 1.0
    return max(logical_pt, int(round(logical_pt * spp)))


def resolve_icon_asset_path(file_name: str) -> Path | None:
    """Path to PNG under assets/icons (PyInstaller: sys._MEIPASS; else project root)."""
    icon_name = (file_name or "").strip()
    if not icon_name:
        return None
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys._MEIPASS) / "assets" / "icons" / icon_name)
    candidates.append(project_root() / "assets" / "icons" / icon_name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resolve_logo_asset_path(file_name: str = "logo.png") -> Path | None:
    """Path to PNG under assets/logo (PyInstaller: sys._MEIPASS; else project root)."""
    name = (file_name or "").strip() or "logo.png"
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys._MEIPASS) / "assets" / "logo" / name)
    candidates.append(project_root() / "assets" / "logo" / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_scaled_photoimage(
    path: Path,
    tk_widget: tk.Misc,
    logical_max_pt: int,
    *,
    scale_with_display_density: bool = True,
) -> tk.PhotoImage | None:
    """
    Load image; long side capped at ``logical_max_pt`` (aspect preserved).

    With ``scale_with_display_density=True`` (default), uses :func:`tk_raster_max_px`
    (denser raster on HiDPI). With ``False``, long side is at most ``logical_max_pt`` pixels.
    """
    if scale_with_display_density:
        max_px = tk_raster_max_px(tk_widget, logical_max_pt)
    else:
        max_px = max(1, int(logical_max_pt))
    try:
        from PIL import Image, ImageTk
    except ImportError:
        return _load_photoimage_tk_subsample(path, max_px)
    try:
        with Image.open(path) as im:
            im.load()
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA")
            w, h = im.size
            if w <= 0 or h <= 0:
                return None
            scale = min(max_px / w, max_px / h)
            nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
            if (nw, nh) != (w, h):
                im = im.resize((nw, nh), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(im)
    except OSError:
        return _load_photoimage_tk_subsample(path, max_px)


def _load_photoimage_tk_subsample(path: Path, max_px: int) -> tk.PhotoImage | None:
    try:
        icon = tk.PhotoImage(file=str(path))
    except tk.TclError:
        return None
    return fit_photoimage_subsample(icon, max_px)


def fit_photoimage_subsample(icon: tk.PhotoImage, max_px: int) -> tk.PhotoImage:
    """Downscale PhotoImage without Pillow (integer subsample)."""
    width = int(icon.width())
    height = int(icon.height())
    if width <= max_px and height <= max_px:
        return icon
    scale_x = max(1, (width + max_px - 1) // max_px)
    scale_y = max(1, (height + max_px - 1) // max_px)
    return icon.subsample(scale_x, scale_y)


def label_with_photoimage(parent: tk.Misc, photo: tk.PhotoImage, **kw) -> tk.Label:
    """Label with image= and a strong ref on the widget (avoid GC dropping the image)."""
    lbl = tk.Label(parent, image=photo, **kw)
    lbl.image = photo
    return lbl


__all__ = [
    "fit_photoimage_subsample",
    "label_with_photoimage",
    "load_scaled_photoimage",
    "resolve_icon_asset_path",
    "tk_raster_max_px",
]
