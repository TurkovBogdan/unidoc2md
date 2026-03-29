"""Base overlay modal: dimmed backdrop and centered card."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.template.styles import (
    MODAL_CARD_MIN_HEIGHT,
    MODAL_CARD_PADX,
    MODAL_CARD_PADY_BOTTOM,
    MODAL_CARD_PADY_TOP,
    MODAL_CARD_WIDTH,
    PALETTE,
)


class OverlayModalBase(ttk.Frame):
    """Dimmed full-area overlay, click blocking, centered card using ``PALETTE``.

    Subclasses implement ``_build_content(container)`` for body, buttons, and inputs.
    """

    def __init__(self, parent: tk.Misc, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._card: tk.Frame | None = None
        self._shade: tk.Frame | None = None
        self._build_overlay()
        self.place_forget()
        self.bind("<Button-1>", lambda _e: "break")

    def _build_overlay(self) -> None:
        p = PALETTE
        self._shade = tk.Frame(self, bg=p["bg_main"], cursor="arrow")
        self._shade.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._shade.bind("<Button-1>", lambda _e: "break")

        self._card = tk.Frame(
            self,
            bg=p["bg_elevated"],
            highlightthickness=1,
            highlightbackground=p["border"],
        )
        self._content = tk.Frame(self._card, bg=p["bg_elevated"])
        self._content.pack(
            fill=tk.BOTH,
            expand=True,
            padx=MODAL_CARD_PADX,
            pady=(MODAL_CARD_PADY_TOP, MODAL_CARD_PADY_BOTTOM),
        )

        self._build_content(self._content)

        self._card.update_idletasks()
        self._content.update_idletasks()
        pady_total = MODAL_CARD_PADY_TOP + MODAL_CARD_PADY_BOTTOM
        req_h = self._content.winfo_reqheight()
        card_h = max(MODAL_CARD_MIN_HEIGHT, req_h + pady_total)
        self._card.place(
            relx=0.5,
            rely=0.5,
            anchor=tk.CENTER,
            width=MODAL_CARD_WIDTH,
            height=card_h,
        )
        self._card.bind("<Button-1>", lambda _e: "break")

    def _build_content(self, container: tk.Misc) -> None:
        """Override in subclasses."""
        pass

    def _update_card_height(self) -> None:
        """Resize the card to fit the current content (e.g. after adding error lines)."""
        self._content.update_idletasks()
        pady_total = MODAL_CARD_PADY_TOP + MODAL_CARD_PADY_BOTTOM
        req_h = self._content.winfo_reqheight()
        card_h = max(MODAL_CARD_MIN_HEIGHT, req_h + pady_total)
        self._card.place_configure(height=card_h)

    def show(self) -> None:
        """Show the modal above its parent. If the parent is the app modal layer, show the layer first."""
        parent = self.master
        if getattr(parent, "_is_app_modal_layer", False) and not parent.winfo_ismapped():
            parent.place(relx=0, rely=0, relwidth=1, relheight=1)
            parent.lift()
        self.lift()
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._update_card_height()
        self.focus_set()
        toplevel = self.winfo_toplevel()
        self._escape_bid = toplevel.bind("<Escape>", lambda _e: self.hide(), add="+")

    def hide(self) -> None:
        """Hide the modal; hide the modal layer when no child modal is visible."""
        toplevel = self.winfo_toplevel()
        try:
            toplevel.unbind("<Escape>", self._escape_bid)
        except (AttributeError, tk.TclError):
            pass
        self.place_forget()
        parent = self.master
        if getattr(parent, "_is_app_modal_layer", False):
            if not any(w.winfo_ismapped() for w in parent.winfo_children()):
                parent.place_forget()
