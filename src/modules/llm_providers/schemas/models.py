"""Schemas for LLM provider model discovery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LLMModelInfo:
    """Normalized information about a provider model."""

    provider: str  # код провайдера
    model: str  # идентификатор модели
    created: int = 0


@dataclass(frozen=True)
class LLMModelsRequest:
    """Request for fetching provider models."""

    provider: str | None = None


@dataclass(frozen=True)
class LLMModelsResponse:
    """Response with normalized provider models."""

    provider: str = ""
    models: tuple[LLMModelInfo, ...] = ()


__all__ = [
    "LLMModelInfo",
    "LLMModelsRequest",
    "LLMModelsResponse",
]