"""Сервис консоли выполнения pipeline для GUI."""

from __future__ import annotations

import queue
import tkinter as tk
from typing import Callable

from src.core.logger import SYSTEM_LOGGER

ConsoleCommand = tuple[str, object | None]


class ProjectPipelineConsole:
    """Thread-safe owner консоли проекта и UI-команд вокруг неё."""

    # Сколько UI-callback'ов снять за один drain до обработки логов (анти starvation).
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
        # Отдельно от append/clear: иначе при лавине логов callback'и (on_run_done и т.д.)
        # висят в хвосте очереди и UI не обновляется.
        self._ui_callbacks: queue.Queue[Callable[[], None]] = queue.Queue()

    def publish(self, text: str) -> None:
        """Публикует строку в консоль из любого потока."""
        self._commands.put(("append", str(text)))

    def clear(self) -> None:
        """Запрашивает очистку консоли из любого потока."""
        try:
            while True:
                self._ui_callbacks.get_nowait()
        except queue.Empty:
            pass
        self._commands.put(("clear", None))

    def call_in_ui(self, callback: Callable[[], None]) -> None:
        """Планирует callback на выполнение в UI-потоке (приоритетнее логов)."""
        self._ui_callbacks.put(callback)

    def attach_system_logger(self) -> None:
        """Подключает глобальный системный логгер к консоли проекта."""
        SYSTEM_LOGGER.set_console_sink(self.publish)

    def detach_system_logger(self) -> None:
        """Отключает глобальный системный логгер от консоли проекта."""
        SYSTEM_LOGGER.set_console_sink(None)

    def drain(self) -> None:
        """Применяет накопленные команды к виджету. Вызывать только из UI-потока."""
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
                SYSTEM_LOGGER.exception("Ошибка в UI-callback консоли pipeline")

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
                    SYSTEM_LOGGER.exception("Ошибка в UI-callback консоли pipeline")

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
