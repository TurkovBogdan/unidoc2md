"""Shared fixtures for llm_models_registry tests."""

from __future__ import annotations

import pytest

from src.modules.llm_models_registry.module import ModuleConfigStore


@pytest.fixture(autouse=True)
def _isolate_llm_models_registry_module_config() -> None:
    ModuleConfigStore.reset()
    yield
    ModuleConfigStore.reset()
