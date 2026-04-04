"""xAI provider initialization tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.llm_providers.providers.clients import XAIProvider


def test_llm_providers_providers_xai():
    config = LLMProvidersConfig(xai_api_key="test-key")
    provider = XAIProvider(config, MagicMock())
    assert isinstance(provider, XAIProvider)
    assert provider.PROVIDER_CODE == "xai"
    assert provider.provider_code == "xai"
