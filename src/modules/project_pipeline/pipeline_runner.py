"""Запуск пайплайна: единая orchestration-точка для этапов проекта."""

from __future__ import annotations

import threading
from typing import Any, Callable

from src.modules.project.project_config import ProjectConfig
from .interfaces import ProjectPipelineLogger
from .models import StageResult
from .pipeline_state_storage import (
    PipelineStateStorage,
    get_default_storage,
)
from .stages import (
    DiscoveryStage,
    ExtractStage,
    ImageProcessingStage,
    MarkdownStage,
    PipelineContext,
    ResultStage,
    TaggingStage,
)

# Порядок этапов пайплайна для оркестратора
PIPELINE_STAGES = [
    DiscoveryStage(),
    ExtractStage(),
    ImageProcessingStage(),
    MarkdownStage(),
    TaggingStage(),
    ResultStage(),
]


class PipelineRunner:
    """Запуск пайплайна по конфигу в одном orchestration thread. Чистый оркестратор: порядок этапов, cancel, fail-fast, статусы."""

    def __init__(self, storage: PipelineStateStorage | None = None) -> None:
        self._storage = storage if storage is not None else get_default_storage()

    def start_run(
        self,
        config: ProjectConfig,
        *,
        on_done: Callable[[bool, str | None], None],
        console_sink: Callable[[str], None] | None = None,
        on_stage_complete: Callable[[str, StageResult], None] | None = None,
        progress_sink: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> None:
        """
        Запускает run() в фоновом потоке. on_done вызывается вызывающей стороной
        через безопасный для неё callback.
        """
        if self._storage.get_current() is not None:
            on_done(False, "Another project is already running.")
            return

        def _run() -> None:
            try:
                success = self.run(
                    config,
                    console_sink=console_sink,
                    on_stage_complete=on_stage_complete,
                    progress_sink=progress_sink,
                )
                if success:
                    on_done(True, None)
                else:
                    on_done(
                        False,
                        "Could not claim run (another project is already running).",
                    )
            except Exception as e:
                from src.core.logger import get_system_logger

                get_system_logger().exception("Pipeline: %s", e)
                if console_sink is not None:
                    console_sink("Error: " + (str(e) or "Pipeline execution failed."))
                on_done(False, str(e) or "Pipeline execution failed.")
                raise

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

    def run(
        self,
        config: ProjectConfig,
        *,
        console_sink: Callable[[str], None] | None = None,
        on_stage_complete: Callable[[str, StageResult], None] | None = None,
        progress_sink: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> bool:
        """
        Синхронный запуск (вызывать из фонового потока).
        Возвращает True при успешном завершении или отмене, False если не удалось захватить запуск.
        Fail-fast: при ошибке этапа или result.success=False пайплайн прерывается, статус failed.
        """
        if not self._storage.claim(config.project_root):
            return False

        try:
            logger = ProjectPipelineLogger(
                config.project_root, console_sink=console_sink
            )
            logger.info("Project started")
            cancel_event = self._storage.get_cancel_event()
            context = PipelineContext(
                config=config,
                logger=logger,
                cancel_event=cancel_event,
                progress_sink=progress_sink,
            )
            stage_input: object = None

            for stage in PIPELINE_STAGES:
                if cancel_event is not None and cancel_event.is_set():
                    self._storage.set_status("cancelled")
                    logger.info("Project stopped")
                    return True
                if not stage.is_enabled(context):
                    continue
                try:
                    stage_result = stage.run(context, stage_input)
                except Exception:
                    self._storage.set_status("failed")
                    raise
                if not stage_result.success:
                    self._storage.set_status("failed")
                    if stage_result.error is not None:
                        raise stage_result.error
                    raise RuntimeError("Stage failed")
                if on_stage_complete is not None:
                    on_stage_complete(stage.stage_id, stage_result)
                stage_input = stage_result.result

            if cancel_event is not None and cancel_event.is_set():
                self._storage.set_status("cancelled")
                logger.info("Project stopped")
            else:
                self._storage.set_status("completed")
                logger.info("Project finished")
        finally:
            self._storage.release()

        return True
