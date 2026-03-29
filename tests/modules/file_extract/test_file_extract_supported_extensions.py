"""Tests for file_extract public API (supported extensions)."""

from __future__ import annotations

from src.modules.file_extract import get_supported_extensions


def test_get_supported_extensions_returns_set() -> None:
    """Public API returns supported extensions without prior module init."""
    exts = get_supported_extensions()
    assert isinstance(exts, set)
    assert ".pdf" in exts
