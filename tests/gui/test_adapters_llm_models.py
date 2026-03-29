"""Tests for llm_models adapter: LLMProviderModelRecord, SyncReport, from_record."""

from __future__ import annotations

import pytest

from src.gui.adapters.llm_models import (
    LLMProviderModelRecord,
    SyncReport,
)


def test_llm_provider_model_record_from_record_minimal() -> None:
    """from_record builds a record from a minimal dict."""
    record = {"provider": "openai", "name": "gpt-4"}
    r = LLMProviderModelRecord.from_record(record)
    assert r.provider_code == "openai"
    assert r.code == "gpt-4"
    assert r.model_key == "openai@gpt-4"
    assert r.enabled is True


def test_llm_provider_model_record_from_record_alternative_keys() -> None:
    """from_record accepts provider_code/code as an alternative to provider/name."""
    record = {"provider_code": "anthropic", "code": "claude-3"}
    r = LLMProviderModelRecord.from_record(record)
    assert r.provider_code == "anthropic"
    assert r.code == "claude-3"


def test_llm_provider_model_record_model_key() -> None:
    """model_key = provider_code@code."""
    r = LLMProviderModelRecord(provider_code="x", code="y")
    assert r.model_key == "x@y"


def test_sync_report_defaults() -> None:
    """SyncReport defaults to zero counts and an empty errors list."""
    report = SyncReport()
    assert report.providers_count == 0
    assert report.models_total == 0
    assert report.models_new == 0
    assert report.errors == []


def test_sync_report_with_errors() -> None:
    """SyncReport keeps the passed-in errors."""
    report = SyncReport(errors=["err1", "err2"])
    assert report.errors == ["err1", "err2"]
