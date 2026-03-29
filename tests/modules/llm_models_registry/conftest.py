"""Shared fixtures for llm_models_registry tests."""

from __future__ import annotations

import pytest

from src.modules.llm_models_registry.module import ModuleConfigStore
from src.modules.llm_models_registry.providers.llm_model_store import reset_llm_model_store


@pytest.fixture(autouse=True)
def _isolate_llm_models_registry_module_config() -> None:
    reset_llm_model_store()
    ModuleConfigStore.reset()
    yield
    reset_llm_model_store()
    ModuleConfigStore.reset()
