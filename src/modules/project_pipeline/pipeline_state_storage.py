"""Хранилище состояния запуска пайплайна: один активный запуск, потокобезопасное, с поддержкой отмены."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunState:
    """Состояние текущего запуска пайплайна."""

    project_root: Path
    status: str  # "running", "completed", "failed", "cancelled"


class PipelineStateStorage:
    """Потокобезопасное хранилище текущего запуска (не более одного). Поддержка request_cancel."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current: RunState | None = None
        self._cancel_event: threading.Event | None = None

    def get_current(self) -> RunState | None:
        """Возвращает текущий запуск или None."""
        with self._lock:
            return self._current

    def claim(self, project_root: Path) -> bool:
        """Захватывает запуск для project_root. Успех только если текущего нет. При успехе создаёт Event для отмены."""
        with self._lock:
            if self._current is not None:
                return False
            self._cancel_event = threading.Event()
            self._current = RunState(project_root=project_root, status="running")
            return True

    def set_status(self, status: str) -> None:
        """Обновляет статус текущего запуска (running/completed/failed/cancelled)."""
        with self._lock:
            if self._current is not None:
                self._current = RunState(
                    project_root=self._current.project_root,
                    status=status,
                )

    def release(self) -> None:
        """Снимает текущий запуск и обнуляет событие отмены."""
        with self._lock:
            self._current = None
            self._cancel_event = None

    def request_cancel(self) -> None:
        """Запрашивает отмену текущего запуска (устанавливает event)."""
        with self._lock:
            if self._cancel_event is not None:
                self._cancel_event.set()

    def get_cancel_event(self) -> threading.Event | None:
        """Возвращает событие отмены текущего запуска (для проверки в run())."""
        with self._lock:
            return self._cancel_event


_default_storage: PipelineStateStorage | None = None


def get_default_storage() -> PipelineStateStorage:
    """Возвращает единственный экземпляр хранилища (для GUI и раннера)."""
    global _default_storage
    if _default_storage is None:
        _default_storage = PipelineStateStorage()
    return _default_storage
