"""Базовый класс этапа пайплайна."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import (
    PipelineContext,
    StageResult,
)


class BasePipelineStage(ABC):
    """
    Базовый контракт этапа пайплайна.
    Каждый этап живёт в своей папке и реализует run(); оркестратор вызывает этапы по порядку,
    проверяет cancel_event и выполняет fail-fast при success=False в StageResult.
    """

    @property
    @abstractmethod
    def stage_id(self) -> str:
        """Идентификатор этапа для логов и регистрации."""
        ...

    def is_enabled(self, context: PipelineContext) -> bool:
        """Пропускать ли этап по конфигу. По умолчанию этап включён."""
        return True

    @abstractmethod
    def run(self, context: PipelineContext, input_result: Any) -> StageResult:
        """
        Выполнить этап. input_result — ``StageResult.result`` предыдущего этапа (или None для первого).
        Возвращать ``StageResult.ok(result=..., payload=...)``: result идёт дальше по цепочке,
        payload — список справочных данных (по умолчанию не передавать — будет ``[]``).
        При ошибке: ``StageResult.fail(result=..., error=...)``.
        """
        ...
