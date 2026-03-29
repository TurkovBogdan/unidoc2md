"""Helpers for llm_models_registry tests."""

from __future__ import annotations

from pathlib import Path

from src.modules.llm_models_registry.module import ModuleConfig, ModuleConfigStore
from src.modules.llm_models_registry.providers.llm_model_store import bind_llm_model_store


def bind_registry(models_store_file: Path) -> None:
    ModuleConfigStore.set(ModuleConfig(models_store_file=models_store_file))
    bind_llm_model_store()
