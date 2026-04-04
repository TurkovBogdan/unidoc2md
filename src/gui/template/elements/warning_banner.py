"""Warning banner: text with a vertical accent line on the left."""

from __future__ import annotations

import tkinter as tk

from src.gui.template.styles import FONT_FAMILY_UI, PALETTE, UI_COLOR_PRIMARY, UI_FONT_SIZE

WARNING_BAR_WIDTH_PX = 4
WARNING_PADX_PX = 10
# Label padding inside strip: slightly tighter top, a bit more below text
WARNING_PADY_PX = (4, 10)
_WRAP_MIN_PX = 40


def gui_element_warning_banner(
    parent: tk.Misc,
    text: str,
    *,
    wraplength: int | None = None,
) -> tk.Frame:
    """
    Warning strip: vertical primary-colored bar on the left, text on the right.
    Returns container for grid/pack.

    Long text wraps when ``wraplength`` is set, or automatically from the container
    width (tk.Label clips one-line text if wraplength stays 0).
    """
    p = PALETTE
    container = tk.Frame(parent, bg=p["bg_surface"])
    bar = tk.Frame(container, width=WARNING_BAR_WIDTH_PX, bg=UI_COLOR_PRIMARY)
    bar.pack(side=tk.LEFT, fill=tk.Y)
    bar.pack_propagate(False)
    initial_wrap = max(_WRAP_MIN_PX, wraplength) if wraplength is not None else 0
    # Asymmetric vertical padding: tk.Label -pady does not accept (top, bottom) on some Tcl builds
    # (TclError: bad screen distance "4 10"); use pack(pady=...) instead.
    label = tk.Label(
        container,
        text=text,
        bg=p["bg_surface"],
        fg=p["text_muted"],
        font=(FONT_FAMILY_UI, UI_FONT_SIZE["extra_small"]),
        anchor=tk.NW,
        justify=tk.LEFT,
        wraplength=initial_wrap,
        padx=WARNING_PADX_PX,
        pady=0,
    )
    label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=WARNING_PADY_PX)

    if wraplength is None:

        def _sync_wraplength(_event: tk.Event[tk.Misc] | None = None) -> None:
            try:
                cw = int(container.winfo_width())
            except (tk.TclError, ValueError):
                return
            if cw <= 1:
                return
            inner = cw - WARNING_BAR_WIDTH_PX - 2 * WARNING_PADX_PX
            label.configure(wraplength=max(_WRAP_MIN_PX, inner))

        container.bind("<Configure>", _sync_wraplength, add="+")
        container.after_idle(_sync_wraplength)

    return container
