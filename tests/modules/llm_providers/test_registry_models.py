"""Tests for the public models(LLMModelsRequest) API."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.modules.llm_providers.module import LLMProvidersConfig, ModuleParams, ModuleStore
from src.modules.llm_providers.errors import LLMProviderDisabledError
from src.modules.llm_providers.providers.clients import MockProvider
from src.modules.llm_providers.providers.llm_provider import LLMProvider, LLMProviderStore
from src.modules.llm_providers.schemas.models import LLMModelsRequest, LLMModelsResponse


@pytest.fixture(autouse=True)
def _reset_llm_providers_store():
    yield
    ModuleStore.reset()
    LLMProviderStore.reset()


def test_models_mock_returns_models_response():
    config = LLMProvidersConfig()
    response_logger = MagicMock()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=response_logger))
    registry = LLMProvider()
    LLMProviderStore.add(MockProvider)
    request = LLMModelsRequest(provider="mock")
    response = registry.models(request)
    assert isinstance(response, LLMModelsResponse)
    assert response.provider == "mock"
    assert len(response.models) == 1
    assert response.models[0].model == "default"
    assert response.models[0].provider == "mock"


def test_models_mock_without_add_raises():
    config = LLMProvidersConfig()
    response_logger = MagicMock()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=response_logger))
    registry = LLMProvider()
    with pytest.raises(LLMProviderDisabledError) as exc_info:
        registry.models(LLMModelsRequest(provider="mock"))
    assert "Unknown" in str(exc_info.value) or "mock" in str(exc_info.value).lower()


def test_models_empty_provider_code_raises_disabled():
    config = LLMProvidersConfig()
    response_logger = MagicMock()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=response_logger))
    registry = LLMProvider()
    with pytest.raises(LLMProviderDisabledError) as exc_info:
        registry.models(LLMModelsRequest(provider=""))
    assert "not specified" in str(exc_info.value).lower() or "provider" in str(exc_info.value).lower()


def test_models_none_provider_code_raises_disabled():
    config = LLMProvidersConfig()
    response_logger = MagicMock()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=response_logger))
    registry = LLMProvider()
    with pytest.raises(LLMProviderDisabledError):
        registry.models(LLMModelsRequest(provider=None))


def test_models_anthropic_disabled_raises_disabled():
    config = LLMProvidersConfig(
        anthropic_provider_enabled=False,
        anthropic_api_key="key",
    )
    response_logger = MagicMock()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=response_logger))
    registry = LLMProvider()
    with pytest.raises(LLMProviderDisabledError) as exc_info:
        registry.models(LLMModelsRequest(provider="anthropic"))
    assert "disabled" in str(exc_info.value).lower()


def test_models_anthropic_no_key_raises_disabled():
    config = LLMProvidersConfig(
        anthropic_provider_enabled=True,
        anthropic_api_key="",
    )
    response_logger = MagicMock()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=response_logger))
    registry = LLMProvider()
    with pytest.raises(LLMProviderDisabledError) as exc_info:
        registry.models(LLMModelsRequest(provider="anthropic"))
    assert "api key" in str(exc_info.value).lower() or "token" in str(exc_info.value).lower()


def test_provider_codes_without_extra():
    config = LLMProvidersConfig()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=None))
    registry = LLMProvider()
    codes = registry._provider_codes_registered()
    assert "mock" not in codes
    assert "anthropic" in codes


def test_provider_codes_after_add_provider():
    config = LLMProvidersConfig()
    ModuleStore.setup(ModuleParams(providers=config, response_logger=None))
    registry = LLMProvider()
    LLMProviderStore.add(MockProvider)
    codes = registry._provider_codes_registered()
    assert "mock" in codes
