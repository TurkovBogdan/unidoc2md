"""LLM provider registry facade: list models via llm_providers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.llm_providers import LLMProvider, LLMProviderDisabledError
from src.modules.llm_providers.schemas.models import LLMModelsRequest

from ..models.llm_model import LLMModel

if TYPE_CHECKING:
    from collections.abc import Sequence


class LLMProvider:
    """
    Thin wrapper over ``src.modules.llm_providers.LLMProvider`` for listing models.
    Converts ``LLMModelInfo`` into ``LLMModel`` with default capabilities.
    """

    def __init__(self) -> None:
        self._registry = LLMProvider()

    def models(self, provider: str) -> Sequence[LLMModel]:
        """
        Return models for the given provider code.
        Raises ``LLMProviderDisabledError`` if the provider is disabled or missing.
        """
        try:
            response = self._registry.models(LLMModelsRequest(provider=provider))
        except LLMProviderDisabledError:
            raise
        return tuple(
            LLMModel(
                provider=info.provider,
                name=info.model,
                created=info.created,
            )
            for info in response.models
        )
