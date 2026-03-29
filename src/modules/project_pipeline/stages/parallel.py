"""Вспомогательный шаблон параллельного выполнения для этапов пайплайна (fail-fast)."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable


def run_parallel_stage(
    *,
    stage_name: str,
    logger: Any,
    task_items: list[tuple[Any, Any]],
    max_workers: int,
    cancel_event: threading.Event | None,
    worker: Callable[[Any], Any],
    handle_result: Callable[[Any, Any], None],
    describe_item: Callable[[Any], str],
    on_progress: Callable[[int, int], None] | None = None,
) -> None:
    """
    Выполняет задачи в пуле потоков. При любой ошибке worker логирует и пробрасывает исключение (fail-fast).
    При cancel_event.is_set() отменяет оставшиеся задачи и выходит.

    Уже запущенные worker'ы после отмены не ждём (shutdown wait=False), иначе
    выход из этапа и release() пайплайна блокируются на долгих HTTP (Vision и т.п.),
    а GUI остаётся с активной кнопкой «Остановить».
    """
    if not task_items:
        logger.info("%s: no tasks", stage_name)
        return
    submitted_total = len(task_items)

    def run_worker(item_meta: Any, item_value: Any) -> Any:
        logger.info("%s: working on %s", stage_name, describe_item(item_meta))
        return worker(item_value)

    executor = ThreadPoolExecutor(max_workers=max_workers)
    # После shutdown(wait=False) нельзя вызывать shutdown(wait=True): в CPython 3.13
    # повторный shutdown всё равно делает join() всех воркеров — снова блокировка на Vision HTTP.
    nonblocking_shutdown_done = False
    try:
        future_to_meta = {
            executor.submit(run_worker, item_meta, item_value): item_meta
            for item_meta, item_value in task_items
            if cancel_event is None or not cancel_event.is_set()
        }
        completed = 0
        for future in as_completed(future_to_meta):
            if cancel_event is not None and cancel_event.is_set():
                # Не использовать `with ThreadPoolExecutor`: при выходе там wait=True
                # и поток оркестратора ждёт все ещё идущие запросы.
                executor.shutdown(wait=False, cancel_futures=True)
                nonblocking_shutdown_done = True
                logger.info("%s: stopped", stage_name)
                break
            item_meta = future_to_meta[future]
            try:
                result = future.result()
            except Exception:
                logger.exception(
                    "%s: error while processing %s",
                    stage_name,
                    describe_item(item_meta),
                )
                raise
            handle_result(item_meta, result)
            completed += 1
            if on_progress is not None:
                on_progress(completed, submitted_total)
            logger.info(
                "%s: completed %s/%s (%s)",
                stage_name,
                completed,
                submitted_total,
                describe_item(item_meta),
            )
    finally:
        if not nonblocking_shutdown_done:
            executor.shutdown(wait=True)
