"""Этап tagging: присвоение тегов документам через LLM после markdown."""

from __future__ import annotations

from .tagging_prompt_builder import TaggingPromptBuilder
from .tagging_result_parser import TaggingResultParser

__all__ = ["TaggingPromptBuilder", "TaggingResultParser", "TaggingStage"]


def __getattr__(name: str):
    if name == "TaggingStage":
        from .stage import TaggingStage

        return TaggingStage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
