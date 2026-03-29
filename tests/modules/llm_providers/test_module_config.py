"""Tests for LLMProvidersConfig, ModuleStore, and store update helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.modules.llm_providers.module import (
    LLMProvidersConfig,
    ModuleParams,
    ModuleStore,
    llm_providers_set_cache_path,
    llm_providers_set_providers_config,
)


@pytest.fixture(autouse=True)
def _reset_module_store() -> None:
    yield
    ModuleStore.reset()


def test_module_store_get_before_setup_raises() -> None:
    with pytest.raises(RuntimeError, match="llm_providers store is not initialized"):
        ModuleStore.get()


def test_is_provider_available_mock_always_true() -> None:
    config = LLMProvidersConfig()
    assert config.is_provider_available("mock") is True


def test_is_provider_available_openai_disabled() -> None:
    config = LLMProvidersConfig(
        openai_provider_enabled=False,
        openai_api_key="sk-xxx",
    )
    assert config.is_provider_available("openai") is False


def test_is_provider_available_openai_enabled_no_key() -> None:
    config = LLMProvidersConfig(
        openai_provider_enabled=True,
        openai_api_key="",
    )
    assert config.is_provider_available("openai") is False


def test_is_provider_available_openai_enabled_whitespace_key() -> None:
    config = LLMProvidersConfig(
        openai_provider_enabled=True,
        openai_api_key="   ",
    )
    assert config.is_provider_available("openai") is False


def test_is_provider_available_openai_enabled_with_key() -> None:
    config = LLMProvidersConfig(
        openai_provider_enabled=True,
        openai_api_key="sk-secret",
    )
    assert config.is_provider_available("openai") is True


def test_is_provider_enabled_alias_matches_available() -> None:
    config = LLMProvidersConfig(
        google_provider_enabled=True,
        google_api_key="k",
    )
    assert config.is_provider_enabled("google") == config.is_provider_available("google")


def test_llm_providers_set_cache_path_preserves_providers_and_logger(tmp_path: Path) -> None:
    cfg = LLMProvidersConfig(openai_provider_enabled=True, openai_api_key="sk")
    log = MagicMock()
    ModuleStore.setup(
        ModuleParams(providers=cfg, response_logger=log, cache_path=None)
    )
    new_cache = tmp_path / "llm-cache"
    llm_providers_set_cache_path(new_cache)

    params = ModuleStore.get()
    assert params.cache_path == new_cache.resolve()
    assert params.providers is cfg
    assert params.response_logger is log


def test_llm_providers_set_providers_config_preserves_cache_and_logger(tmp_path: Path) -> None:
    old_cfg = LLMProvidersConfig()
    new_cfg = LLMProvidersConfig(
        anthropic_provider_enabled=True,
        anthropic_api_key="sk-ant",
    )
    log = MagicMock()
    ModuleStore.setup(
        ModuleParams(
            providers=old_cfg,
            response_logger=log,
            cache_path=tmp_path,
        )
    )
    llm_providers_set_providers_config(new_cfg)

    params = ModuleStore.get()
    assert params.providers is new_cfg
    assert params.cache_path == tmp_path.resolve()
    assert params.response_logger is log
