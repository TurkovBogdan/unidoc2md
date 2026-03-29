"""
Load model lists from providers and append new rows to the registry.
Raw API response logging happens only in the provider client layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.modules.llm_providers import LLMProvider, LLMModelsRequest

from .llm_model_manager import LLMModelManager


@dataclass
class SyncModelsResult:
    """Outcome of syncing the registry with providers."""

    providers_count: int = 0
    models_total: int = 0
    models_new: int = 0
    errors: list[str] = field(default_factory=list)


class SyncModelRegistryService:
    """
    Static sync service for the model registry.
    Registry path is set at boot.
    Reads provider codes from LLMProvider (config from module store), fetches models per provider.
    Models missing from the registry are added with defaults: can_update=True, enabled=True, created.
    """

    @staticmethod
    def sync_models() -> SyncModelsResult:
        """
        For each available provider, fetch models; add missing rows with can_update=True,
        enabled=True, created.
        Returns counts: providers touched, total models seen, newly added rows.
        """
        registry = LLMProvider()
        manager = LLMModelManager()
        to_add: list[dict] = []
        providers_count = 0
        models_total = 0

        errors: list[str] = []
        for provider_code in registry.provider_codes():
            try:
                response = registry.models(LLMModelsRequest(provider=provider_code))
            except Exception as e:
                errors.append(f"{provider_code}: {e}")
                continue
            providers_count += 1
            for model_info in response.models:
                models_total += 1
                model_key = f"{model_info.provider}@{model_info.model}"
                if manager.exists(model_key):
                    continue
                record = manager.create_empty(model_key, created=model_info.created)
                to_add.append(record)

        models_new = manager.add_models(to_add)
        return SyncModelsResult(
            providers_count=providers_count,
            models_total=models_total,
            models_new=models_new,
            errors=errors,
        )
