"""Tests for ChatRequestSerializer and response dict helpers."""

from __future__ import annotations

import json

import pytest

from src.modules.llm_providers.schemas.chat import (
    LLMChatMessage,
    LLMChatMessageImage,
    LLMChatMessageText,
    LLMChatReasoningEffort,
    LLMChatRequest,
    LLMChatRole,
)
from src.modules.llm_providers.services.chat_serializer import (
    ChatRequestSerializer,
    _response_from_dict,
    _response_to_dict,
)


def test_chat_request_json_roundtrip() -> None:
    req = LLMChatRequest(
        provider="openai",
        model="gpt-4o-mini",
        messages=[
            LLMChatMessage(
                role=LLMChatRole.USER,
                content=[
                    LLMChatMessageText(message="hello"),
                    LLMChatMessageImage(mime="image/png", base64="AAA"),
                ],
            )
        ],
        max_tokens=512,
        temperature=0.7,
        top_p=0.9,
        reasoning=LLMChatReasoningEffort.LOW,
        stream=True,
    )
    s = ChatRequestSerializer.to_json(req)
    back = ChatRequestSerializer.from_json(s)
    assert back.provider == req.provider
    assert back.model == req.model
    assert back.max_tokens == req.max_tokens
    assert back.temperature == req.temperature
    assert back.top_p == req.top_p
    assert back.reasoning == req.reasoning
    assert back.stream is True
    assert len(back.messages) == 1
    assert back.messages[0].role == LLMChatRole.USER
    assert isinstance(back.messages[0].content[0], LLMChatMessageText)
    assert back.messages[0].content[0].message == "hello"
    assert isinstance(back.messages[0].content[1], LLMChatMessageImage)
    assert back.messages[0].content[1].mime == "image/png"
    assert back.messages[0].content[1].base64 == "AAA"


def test_cache_key_stable_for_same_request() -> None:
    req = LLMChatRequest(
        provider="p",
        model="m",
        messages=[
            LLMChatMessage(
                role=LLMChatRole.USER,
                content=[LLMChatMessageText(message="x")],
            )
        ],
    )
    k1 = ChatRequestSerializer.cache_key(req)
    k2 = ChatRequestSerializer.cache_key(req)
    assert k1 == k2
    assert len(k1) == 32


def test_to_json_deterministic_sort_keys() -> None:
    req = LLMChatRequest(
        provider="a",
        model="b",
        messages=[
            LLMChatMessage(
                role=LLMChatRole.USER,
                content=[LLMChatMessageText(message="z")],
            )
        ],
    )
    j1 = ChatRequestSerializer.to_json_deterministic(req)
    j2 = ChatRequestSerializer.to_json_deterministic(req)
    assert j1 == j2
    parsed = json.loads(j1)
    assert list(parsed.keys()) == sorted(parsed.keys())


def test_response_dict_roundtrip_preserves_cache_true() -> None:
    msg = LLMChatMessage(
        role=LLMChatRole.ASSISTANT,
        content=[LLMChatMessageText(message="ok")],
    )
    original = _response_from_dict(
        {
            "finish_reason": "stop",
            "created": 9,
            "message": {"role": "assistant", "content": [{"type": "text", "text": "ok"}]},
            "message_reasoning": "r",
            "response_id": "rid",
            "tokens_usage": {
                "prompt": 1,
                "reasoning": 2,
                "completion": 3,
                "total": 6,
            },
            "cache": True,
        }
    )
    data = _response_to_dict(original)
    again = _response_from_dict(data)
    assert again.finish_reason == "stop"
    assert again.created == 9
    assert again.message is not None
    assert again.cache is True
    assert again.response_id == "rid"
    assert again.tokens_usage is not None
    assert again.tokens_usage.total == 6
