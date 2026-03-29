"""Exceptions for the llm_models_registry module."""

from __future__ import annotations


class LLMModelsRegistryError(Exception):
    """Base registry error; optional ``cause`` on subclasses."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class EmptyProviderError(LLMModelsRegistryError):
    """Provider must not be empty."""


class EmptyModelCodeError(LLMModelsRegistryError):
    """Model code must not be empty."""
