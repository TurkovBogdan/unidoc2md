"""Google provider initialization tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.llm_providers.providers.clients import GoogleProvider


def test_llm_providers_providers_google():
    config = LLMProvidersConfig(google_api_key="test-key")
    provider = GoogleProvider(config, MagicMock())
    assert isinstance(provider, GoogleProvider)
    assert provider.PROVIDER_CODE == "google"
    assert provider.provider_code == "google"
