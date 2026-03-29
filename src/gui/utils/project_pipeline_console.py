"""Pipeline execution console bridge for the GUI."""

from __future__ import annotations

import queue
import tkinter as tk
from typing import Callable

from src.core.logger import SYSTEM_LOGGER

ConsoleCommand = tuple[str, object | None]


class ProjectPipelineConsole:
    """Thread-safe console owner and UI command queue for project pipeline output."""

    # UI callbacks to drain per pump before log lines (avoid starving UI updates).
    _UI_DRAIN_MAX_PER_PUMP = 500

    def __init__(
        self,
        text_widget: tk.Text,
        *,
        max_lines: int = 2000,
        drain_batch_size: int = 100,
    ) -> None:
        self._text_widget = text_widget
        self._max_lines = max_lines
        self._drain_batch_size = drain_batch_size
        self._commands: queue.Queue[ConsoleCommand] = queue.Queue()
        # Separate from append/clear: under log flood, trailing callbacks (on_run_done, etc.)
        # would stall and the UI would not refresh.
        self._ui_callbacks: queue.Queue[Callable[[], None]] = queue.Queue()

    def publish(self, text: str) -> None:
        """Enqueue a line from any thread."""
        self._commands.put(("append", str(text)))

    def clear(self) -> None:
        """Request console clear from any thread."""
        try:
            while True:
                self._ui_callbacks.get_nowait()
        except queue.Empty:
            pass
        self._commands.put(("clear", None))

    def call_in_ui(self, callback: Callable[[], None]) -> None:
        """Schedule a callback on the UI thread (processed before log lines)."""
        self._ui_callbacks.put(callback)

    def attach_system_logger(self) -> None:
        """Route global system logger output into this console."""
        SYSTEM_LOGGER.set_console_sink(self.publish)

    def detach_system_logger(self) -> None:
        """Stop routing global system logger into this console."""
        SYSTEM_LOGGER.set_console_sink(None)

    def drain(self) -> None:
        """Apply queued commands to the widget. Call only from the UI thread."""
        if not self._text_widget.winfo_exists():
            return

        for _ in range(self._UI_DRAIN_MAX_PER_PUMP):
            try:
                cb = self._ui_callbacks.get_nowait()
            except queue.Empty:
                break
            try:
                cb()
            except Exception:
                SYSTEM_LOGGER.exception("Pipeline console UI callback failed")

        append_batch: list[str] = []
        for _ in range(self._drain_batch_size):
            try:
                command, payload = self._commands.get_nowait()
            except queue.Empty:
                break

            if command == "append":
                append_batch.append(str(payload or ""))
                continue

            self._flush_append_batch(append_batch)
            append_batch = []

            if command == "clear":
                self._clear_widget()
            elif command == "call" and callable(payload):
                try:
                    payload()
                except Exception:
                    SYSTEM_LOGGER.exception("Pipeline console UI callback failed")

        self._flush_append_batch(append_batch)

    def _flush_append_batch(self, batch: list[str]) -> None:
        if not batch:
            return
        self._text_widget.config(state=tk.NORMAL)
        self._text_widget.insert(tk.END, "\n".join(batch) + "\n")
        self._trim_log_lines()
        self._text_widget.see(tk.END)
        self._text_widget.config(state=tk.DISABLED)

    def _clear_widget(self) -> None:
        self._text_widget.config(state=tk.NORMAL)
        self._text_widget.delete("1.0", tk.END)
        self._text_widget.config(state=tk.DISABLED)

    def _trim_log_lines(self) -> None:
        last_line = int(self._text_widget.index("end-1c").split(".")[0])
        extra_lines = last_line - self._max_lines
        if extra_lines > 0:
            self._text_widget.delete("1.0", f"{extra_lines + 1}.0")
