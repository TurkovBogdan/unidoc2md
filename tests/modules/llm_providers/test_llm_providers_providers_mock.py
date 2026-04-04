"""Mock provider initialization tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.llm_providers.providers.clients import MockProvider


def test_llm_providers_providers_mock():
    config = LLMProvidersConfig()
    provider = MockProvider(config, MagicMock())
    assert isinstance(provider, MockProvider)
    assert provider.PROVIDER_CODE == "mock"
    assert provider.provider_code == "mock"
