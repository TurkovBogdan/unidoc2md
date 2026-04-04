"""LM Studio provider initialization tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.llm_providers.providers.clients import LMStudioProvider


def test_llm_providers_providers_lmstudio():
    config = LLMProvidersConfig(
        lmstudio_host="127.0.0.1",
        lmstudio_port="1234",
        lmstudio_ssl=False,
    )
    provider = LMStudioProvider(config, MagicMock())
    assert isinstance(provider, LMStudioProvider)
    assert provider.PROVIDER_CODE == "lmstudio"
    assert provider.provider_code == "lmstudio"
