"""Tests for ModuleConfigStore and LLMModelManager when the module is not bootstrapped."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.llm_models_registry.errors import EmptyModelCodeError, EmptyProviderError
from src.modules.llm_models_registry.module import ModuleConfig, ModuleConfigStore
from src.modules.llm_models_registry.services.llm_model_manager import LLMModelManager
from tests.modules.llm_models_registry.support import bind_registry


def test_module_config_store_get_before_set_raises() -> None:
    with pytest.raises(RuntimeError, match="llm_models_registry module is not initialized"):
        ModuleConfigStore.get()


def test_llm_model_manager_requires_bootstrapped_module() -> None:
    with pytest.raises(RuntimeError, match="llm_models_registry module is not initialized"):
        LLMModelManager()


def test_llm_model_manager_requires_bound_store(tmp_path: Path) -> None:
    ModuleConfigStore.set(ModuleConfig(models_store_file=tmp_path / "reg.json"))
    with pytest.raises(RuntimeError, match="llm_models_registry.store_not_bound"):
        LLMModelManager()


def test_get_model_names_empty_provider_raises(tmp_path: Path) -> None:
    bind_registry(tmp_path / "models.json")
    manager = LLMModelManager()
    with pytest.raises(EmptyProviderError):
        manager.get_model_names("")


def test_get_model_openai_at_without_model_raises(tmp_path: Path) -> None:
    bind_registry(tmp_path / "reg.json")
    manager = LLMModelManager()
    with pytest.raises(EmptyModelCodeError):
        manager.get_model("openai@")
