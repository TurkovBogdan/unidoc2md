"""Base exception hierarchy for LLM providers."""

from __future__ import annotations


class LLMProviderError(Exception):
    """Base exception for all provider-related failures."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class LLMProviderClientError(LLMProviderError):
    """Base exception for provider client/API interaction failures."""


class LLMProviderAuthError(LLMProviderClientError):
    """Authentication failure such as 401, 403, or an invalid key."""


class LLMProviderRateLimitError(LLMProviderClientError):
    """Provider rate limit was exceeded (429)."""


class LLMProviderTransportError(LLMProviderClientError):
    """Transport-level failure such as timeout or connection error."""


class LLMProviderResponseError(LLMProviderClientError):
    """Invalid or unexpected API response."""


class LLMProviderContentFilterError(LLMProviderClientError):
    """Response blocked by provider content policy (e.g. promptFeedback.blockReason in Gemini)."""


class LLMProviderDisabledError(LLMProviderError):
    """Provider is disabled or API key/token is not set."""


__all__ = [
    "LLMProviderError",
    "LLMProviderClientError",
    "LLMProviderAuthError",
    "LLMProviderContentFilterError",
    "LLMProviderDisabledError",
    "LLMProviderRateLimitError",
    "LLMProviderResponseError",
    "LLMProviderTransportError",
]
