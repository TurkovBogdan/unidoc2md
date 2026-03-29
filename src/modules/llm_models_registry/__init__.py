"""Local LLM model registry: load, sync with providers, persist."""

from __future__ import annotations

from .bootstrap import module_llm_model_registry_boot
from .errors import EmptyModelCodeError, EmptyProviderError, LLMModelsRegistryError
from .module import ModuleConfig, ModuleConfigStore
from .services import (
    LLMModelManager,
    SyncModelRegistryService,
    SyncModelsResult,
)

__all__ = [
    "EmptyModelCodeError",
    "EmptyProviderError",
    "LLMModelManager",
    "LLMModelsRegistryError",
    "ModuleConfig",
    "ModuleConfigStore",
    "SyncModelRegistryService",
    "SyncModelsResult",
    "module_llm_model_registry_boot",
]
