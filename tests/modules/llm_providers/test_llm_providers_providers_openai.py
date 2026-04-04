"""OpenAI provider initialization tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.llm_providers.providers.clients import OpenAIProvider


def test_llm_providers_providers_openai():
    config = LLMProvidersConfig(openai_api_key="test-key")
    provider = OpenAIProvider(config, MagicMock())
    assert isinstance(provider, OpenAIProvider)
    assert provider.PROVIDER_CODE == "openai"
    assert provider.provider_code == "openai"
