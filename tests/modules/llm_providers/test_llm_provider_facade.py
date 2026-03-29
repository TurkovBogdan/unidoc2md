"""Tests for LLMProvider facade, LLMProviderStore, and chat + file cache integration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.modules.llm_providers.errors import LLMProviderDisabledError
from src.modules.llm_providers.module import LLMProvidersConfig, ModuleParams, ModuleStore
from src.modules.llm_providers.providers.clients import MockProvider
from src.modules.llm_providers.providers.llm_provider import LLMProvider, LLMProviderStore
from src.modules.llm_providers.schemas.chat import (
    LLMChatMessage,
    LLMChatMessageText,
    LLMChatRequest,
    LLMChatResponse,
    LLMChatRole,
)


@pytest.fixture(autouse=True)
def _reset_stores() -> None:
    yield
    ModuleStore.reset()
    LLMProviderStore.reset()


def _sample_request() -> LLMChatRequest:
    return LLMChatRequest(
        provider="mock",
        model="default",
        messages=[
            LLMChatMessage(
                role=LLMChatRole.USER,
                content=[LLMChatMessageText(message="ping")],
            )
        ],
    )


def _sample_response() -> LLMChatResponse:
    return LLMChatResponse(
        finish_reason="stop",
        created=100,
        message=LLMChatMessage(
            role=LLMChatRole.ASSISTANT,
            content=[LLMChatMessageText(message="pong")],
        ),
        cache=False,
    )


def test_get_provider_unknown_code_raises() -> None:
    ModuleStore.setup(ModuleParams(providers=LLMProvidersConfig(), response_logger=None))
    registry = LLMProvider()
    with pytest.raises(LLMProviderDisabledError, match="Unknown"):
        registry.get_provider("nonexistent_provider_xyz")


def test_chat_empty_provider_raises() -> None:
    ModuleStore.setup(ModuleParams(providers=LLMProvidersConfig(), response_logger=None))
    LLMProviderStore.add(MockProvider)
    registry = LLMProvider()
    req = LLMChatRequest(
        provider="",
        model="m",
        messages=[
            LLMChatMessage(
                role=LLMChatRole.USER,
                content=[LLMChatMessageText(message="x")],
            )
        ],
    )
    with pytest.raises(LLMProviderDisabledError, match="not specified"):
        registry.chat(req)


def test_provider_codes_filters_by_config() -> None:
    ModuleStore.setup(ModuleParams(providers=LLMProvidersConfig(), response_logger=None))
    registry = LLMProvider()
    LLMProviderStore.add(MockProvider)
    # mock is always "available" in config; others need keys
    codes = registry.provider_codes()
    assert "mock" in codes
    assert "openai" not in codes

    cfg = LLMProvidersConfig(
        openai_provider_enabled=True,
        openai_api_key="sk-test",
    )
    ModuleStore.setup(ModuleParams(providers=cfg, response_logger=None))
    codes2 = registry.provider_codes()
    assert "mock" in codes2
    assert "openai" in codes2


def test_llm_provider_store_reset_removes_added_provider() -> None:
    assert "mock" not in LLMProviderStore.provider_codes()
    LLMProviderStore.add(MockProvider)
    assert "mock" in LLMProviderStore.provider_codes()
    LLMProviderStore.reset()
    assert "mock" not in LLMProviderStore.provider_codes()
    assert "openai" in LLMProviderStore.provider_codes()


def test_llm_provider_set_cache_path_updates_store(tmp_path: Path) -> None:
    ModuleStore.setup(
        ModuleParams(providers=LLMProvidersConfig(), response_logger=None, cache_path=None)
    )
    registry = LLMProvider()
    sub = tmp_path / "new_cache"
    registry.set_cache_path(sub)
    assert ModuleStore.get().cache_path == sub.resolve()


def test_chat_with_cache_writes_then_reads_from_disk(tmp_path: Path) -> None:
    ModuleStore.setup(
        ModuleParams(
            providers=LLMProvidersConfig(),
            response_logger=MagicMock(),
            cache_path=tmp_path,
        )
    )
    LLMProviderStore.add(MockProvider)
    registry = LLMProvider()
    req = _sample_request()
    resp = _sample_response()
    api_calls: list[None] = []

    def _fake_chat(self: MockProvider, request: LLMChatRequest, *, cache: bool = False) -> LLMChatResponse:
        assert request.provider == "mock"
        api_calls.append(None)
        return resp

    with patch.object(MockProvider, "chat", _fake_chat):
        out1 = registry.chat(req, cache=False)
        assert out1.cache is False
        assert out1.message is not None
        assert out1.message.content[0].message == "pong"  # type: ignore[union-attr]
        assert len(api_calls) == 1

        out2 = registry.chat(req, cache=True)
        assert len(api_calls) == 1

    assert out2.cache is True
    assert out2.message is not None
    assert out2.message.content[0].message == "pong"  # type: ignore[union-attr]


def test_chat_without_cache_path_passes_cache_flag_to_provider() -> None:
    ModuleStore.setup(
        ModuleParams(providers=LLMProvidersConfig(), response_logger=MagicMock(), cache_path=None)
    )
    LLMProviderStore.add(MockProvider)
    registry = LLMProvider()
    req = _sample_request()
    resp = _sample_response()

    def _fake_chat(self: MockProvider, request: LLMChatRequest, *, cache: bool = False) -> LLMChatResponse:
        assert cache is True
        return resp

    with patch.object(MockProvider, "chat", _fake_chat):
        out = registry.chat(req, cache=True)
    assert out is resp
