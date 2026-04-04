"""Anthropic provider initialization tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.llm_providers.providers.clients import AnthropicProvider


def test_llm_providers_providers_anthropic():
    config = LLMProvidersConfig(anthropic_api_key="test-key")
    provider = AnthropicProvider(config, MagicMock())
    assert isinstance(provider, AnthropicProvider)
    assert provider.PROVIDER_CODE == "anthropic"
    assert provider.provider_code == "anthropic"
