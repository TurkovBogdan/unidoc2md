"""Run-scoped lock helpers for pipeline stages."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator


class PipelineLockCancelled(RuntimeError):
    """Lock wait interrupted by pipeline cancellation."""


@dataclass(frozen=True)
class PipelineRunLocker:
    """Lock container bound to a single pipeline run."""

    vision_call_lock: threading.Lock

    @classmethod
    def create(cls) -> "PipelineRunLocker":
        return cls(vision_call_lock=threading.Lock())

    @contextmanager
    def vision_call(
        self, *, cancel_event: threading.Event | None = None
    ) -> Iterator[None]:
        """
        Acquire a run-local lock for cache-path-sensitive Vision LLM calls.

        Waiting is interruptible by ``cancel_event`` to avoid long stalls while
        a stage is being cancelled.
        """
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise PipelineLockCancelled("Pipeline call lock wait cancelled")
            if self.vision_call_lock.acquire(timeout=0.1):
                break
        try:
            yield
        finally:
            self.vision_call_lock.release()
