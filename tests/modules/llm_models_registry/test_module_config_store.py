"""Tests for ModuleConfigStore and LLMModelManager when the module is not bootstrapped."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.llm_models_registry.errors import EmptyModelCodeError, EmptyProviderError
from src.modules.llm_models_registry.module import ModuleConfig, ModuleConfigStore
from src.modules.llm_models_registry.services.llm_model_manager import LLMModelManager


def test_module_config_store_get_before_set_raises() -> None:
    with pytest.raises(RuntimeError, match="llm_models_registry module is not initialized"):
        ModuleConfigStore.get()


def test_llm_model_manager_without_path_requires_bootstrapped_module() -> None:
    with pytest.raises(RuntimeError, match="llm_models_registry module is not initialized"):
        LLMModelManager()


def test_llm_model_manager_with_explicit_path_works_without_module_config(tmp_path: Path) -> None:
    path = tmp_path / "reg.json"
    manager = LLMModelManager(store_file_path=path)
    assert manager.store.store_file_path == path.resolve()


def test_get_model_names_empty_provider_raises(tmp_path: Path) -> None:
    ModuleConfigStore.set(ModuleConfig(models_store_file=tmp_path / "models.json"))
    manager = LLMModelManager()
    with pytest.raises(EmptyProviderError):
        manager.get_model_names("")


def test_get_record_openai_at_without_model_raises(tmp_path: Path) -> None:
    manager = LLMModelManager(store_file_path=tmp_path / "reg.json")
    with pytest.raises(EmptyModelCodeError):
        manager.get_record("openai@")
