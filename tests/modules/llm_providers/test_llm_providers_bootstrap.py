"""Tests for module_llm_providers_boot."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.modules.llm_providers.bootstrap import module_llm_providers_boot
from src.modules.llm_providers.module import LLMProvidersConfig, ModuleStore


@pytest.fixture(autouse=True)
def _reset_module_store() -> None:
    yield
    ModuleStore.reset()


def test_boot_sets_store_and_disables_cache_when_no_path() -> None:
    config = LLMProvidersConfig()
    module_llm_providers_boot(config)

    params = ModuleStore.get()
    assert params.providers is config
    assert params.cache_path is None
    assert params.response_logger is None


def test_boot_creates_cache_directory(tmp_path: Path) -> None:
    cache_dir = tmp_path / "nested" / "cache"
    assert not cache_dir.exists()

    config = LLMProvidersConfig()
    log = MagicMock()
    module_llm_providers_boot(config, response_logger=log, cache_path=cache_dir)

    assert cache_dir.is_dir()
    params = ModuleStore.get()
    assert params.cache_path == cache_dir.resolve()
    assert params.response_logger is log
