"""Screen registry: maps ``screen_code`` to the frame used for navigation."""

from __future__ import annotations

from tkinter import ttk


class ScreenRegistry:
    """Holds registered screens by code for the router to pack/unpack."""

    def __init__(self) -> None:
        self._frames: dict[str, ttk.Frame] = {}

    def register(self, screen_code: str, frame: ttk.Frame) -> None:
        self._frames[screen_code] = frame

    def get(self, screen_code: str) -> ttk.Frame | None:
        return self._frames.get(screen_code)

    def has(self, screen_code: str) -> bool:
        return screen_code in self._frames

    def names(self) -> set[str]:
        return set(self._frames.keys())
