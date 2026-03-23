"""Use-case: запуск и отмена выполнения pipeline проекта."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from src.modules.project import load_project_config
from src.modules.project_pipeline.pipeline_runner import PipelineRunner

if TYPE_CHECKING:
    from typing import Any

    from src.modules.project_pipeline.models import StageResult
    from src.modules.project_pipeline.pipeline_state_storage import PipelineStateStorage


def start_pipeline(
    project_root: Path,
    pipeline_storage: PipelineStateStorage,
    console_sink: Callable[[str], None] | None,
    on_done: Callable[[bool, str | None], None],
    *,
    on_stage_complete: Callable[[str, "StageResult"], None] | None = None,
    progress_sink: Callable[[str, dict[str, Any]], None] | None = None,
) -> None:
    """
    Запускает pipeline для проекта в фоне. on_done(success, message) вызывается по завершении.
    """
    config = load_project_config(project_root)
    runner = PipelineRunner(pipeline_storage)
    runner.start_run(
        config,
        on_done=on_done,
        console_sink=console_sink,
        on_stage_complete=on_stage_complete,
        progress_sink=progress_sink,
    )


def request_cancel(pipeline_storage: PipelineStateStorage) -> None:
    """Запрашивает отмену текущего выполнения."""
    pipeline_storage.request_cancel()
