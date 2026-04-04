"""
Tk on Windows: creating a second ``tk.Tk()`` after the first was destroyed often breaks Tcl
(missing tk.tcl / panedwindow.tcl). GUI tests share one hidden root for the whole session.
"""

from __future__ import annotations

import tkinter as tk

import pytest

_original_Tk = tk.Tk
_shared_root: tk.Tk | None = None


@pytest.fixture(scope="session", autouse=True)
def _tk_single_root_for_gui_package() -> None:
    """Force ``tk.Tk()`` to return one withdrawn root for all tests under ``tests/gui/``."""
    global _shared_root
    _shared_root = _original_Tk()
    _shared_root.withdraw()

    def _Tk(*args: object, **kwargs: object) -> tk.Tk:
        assert _shared_root is not None
        return _shared_root

    tk.Tk = _Tk  # type: ignore[misc, assignment]

    yield

    tk.Tk = _original_Tk
    try:
        if _shared_root is not None and _shared_root.winfo_exists():
            _shared_root.destroy()
    except tk.TclError:
        pass
    _shared_root = None
