"""Loader layout slot: full-screen frame for the startup / loading screen."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_loader_slot(parent: tk.Misc) -> ttk.Frame:
    """Create the loader screen slot. ``parent`` is the layout container."""
    return ttk.Frame(parent)
