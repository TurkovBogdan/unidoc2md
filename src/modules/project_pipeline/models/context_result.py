"""Модели контекста выполнения этапа и результата этапа."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.modules.project.project_config import ProjectConfig

from ..interfaces.logger import PipelineLoggerProtocol

# UI / наблюдатели: stage_id и произвольный словарь (без привязки к тексту лога).
# extract: documents_done, documents_total.
# image_processing: images_done, images_total, logic, vision (как в payload этапа).
# result: documents_done, documents_total (сохранение .md в result, опционально index.md).
PipelineProgressSink = Callable[[str, dict[str, Any]], None]


@dataclass(frozen=True)
class PipelineContext:
    """Контекст выполнения этапа: конфиг, логгер, событие отмены, опционально sink прогресса."""

    config: ProjectConfig
    logger: PipelineLoggerProtocol
    cancel_event: threading.Event | None
    progress_sink: PipelineProgressSink | None = None


@dataclass
class StageResult:
    """
    Результат выполнения этапа.

    - ``result`` — выход этапа, передаётся следующему этапу (цепочка пайплайна).
    - ``payload`` — справочные данные (список); по умолчанию ``[]``. Не прокидывается оркестратором дальше.
      Для **discovery**: ``payload[0]`` — число найденных файлов (``int``), при отсутствии файлов — ``[0]``.
      Для **extract**: список чисел ``docs_done``, ``total``, фрагменты, изображения, …
      Для **image_processing**: ``payload[0]`` — ``dict`` с полями ``logic``, ``vision`` (сводка vision/OCR для UI).
      Для **markdown** (при LLM): ``payload[0]`` — ``dict`` с полями ``logic``, ``llm`` (токены/кеш/API/стоимость для UI).
    При success=False runner выполняет fail-fast.
    """

    result: Any
    payload: list[Any] = field(default_factory=list)
    success: bool = True
    error: Exception | None = None

    @classmethod
    def ok(cls, result: Any, *, payload: list[Any] | None = None) -> StageResult:
        pl: list[Any] = [] if payload is None else list(payload)
        return cls(result=result, payload=pl, success=True, error=None)

    @classmethod
    def fail(
        cls,
        result: Any,
        error: Exception,
        *,
        payload: list[Any] | None = None,
    ) -> StageResult:
        pl: list[Any] = [] if payload is None else list(payload)
        return cls(result=result, payload=pl, success=False, error=error)
