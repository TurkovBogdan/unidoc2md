"""Tests for llm_providers exception types."""

from __future__ import annotations

import json

from src.modules.llm_providers.errors import (
    LLMProviderAuthError,
    LLMProviderClientError,
    LLMProviderError,
)


def test_llm_provider_error_stores_cause() -> None:
    inner = ValueError("inner")
    err = LLMProviderError("wrapper", cause=inner)
    assert str(err) == "wrapper"
    assert err.cause is inner


def test_client_error_subclass_inheritance() -> None:
    cause = json.JSONDecodeError("msg", "doc", 0)
    err = LLMProviderAuthError("unauthorized", cause=cause)
    assert isinstance(err, LLMProviderClientError)
    assert isinstance(err, LLMProviderError)
    assert err.cause is cause
