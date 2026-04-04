"""gui_element_warning_banner: Tcl-safe construction (e.g. Label pady on Windows)."""

from __future__ import annotations

import tkinter as tk

import pytest

from src.gui.template.elements.warning_banner import gui_element_warning_banner


@pytest.fixture
def tk_root() -> tk.Tk:
    """
    ``tests/gui/conftest`` makes ``tk.Tk()`` a session singleton; never call ``destroy()`` on it.
    Drop only widgets created during the test.
    """
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        for w in list(root.winfo_children()):
            w.destroy()
        root.withdraw()
    except tk.TclError:
        pass


def test_warning_banner_creates_without_tcl_error(tk_root: tk.Tk) -> None:
    """Regression: Label(..., pady=(a,b)) raised TclError on Windows; widget must build."""
    frame = tk.Frame(tk_root)
    frame.pack()
    banner = gui_element_warning_banner(frame, "Short text")
    tk_root.update_idletasks()
    assert banner.winfo_exists()
    children = banner.winfo_children()
    assert len(children) >= 2


def test_warning_banner_long_text_and_dynamic_wrap(tk_root: tk.Tk) -> None:
    """Dynamic wraplength path configures without error after layout."""
    frame = tk.Frame(tk_root, width=400, height=120)
    frame.pack_propagate(False)
    frame.pack()
    long_text = "word " * 40 + "end."
    banner = gui_element_warning_banner(frame, long_text, wraplength=None)
    tk_root.update_idletasks()
    assert banner.winfo_exists()


def test_warning_banner_explicit_wraplength(tk_root: tk.Tk) -> None:
    frame = tk.Frame(tk_root)
    frame.pack()
    banner = gui_element_warning_banner(frame, "x", wraplength=200)
    tk_root.update_idletasks()
    assert banner.winfo_exists()
