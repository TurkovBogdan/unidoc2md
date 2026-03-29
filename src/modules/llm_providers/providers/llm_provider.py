"""Registry for resolving LLM providers by provider_code."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..module import ModuleStore, llm_providers_set_cache_path
from ..errors import LLMProviderDisabledError
from ..interfaces.provider_client import BaseProviderClient
from ..schemas.chat import LLMChatRequest, LLMChatResponse
from ..schemas.models import LLMModelsRequest, LLMModelsResponse
from ..services.chat_request_cache import LLMChatRequestCache

from .clients import (
    AnthropicProvider,
    GoogleProvider,
    OpenAIProvider,
    XAIProvider,
    LMStudioProvider,
)

_PROVIDER_CLASSES: tuple[type[BaseProviderClient], ...] = (
    AnthropicProvider,
    GoogleProvider,
    OpenAIProvider,
    XAIProvider,
    LMStudioProvider,
)


class LLMProviderStore:
    """Static store of provider classes: default set, add, reset."""

    _default: dict[str, type[BaseProviderClient]] = {
        cls.PROVIDER_CODE: cls for cls in _PROVIDER_CLASSES
    }
    _current: dict[str, type[BaseProviderClient]] = dict(_default)

    @classmethod
    def get_class(cls, provider_code: str) -> type[BaseProviderClient] | None:
        """Return provider class by code or None."""
        return cls._current.get(provider_code)

    @classmethod
    def provider_codes(cls) -> list[str]:
        """All registered provider codes."""
        return list(cls._current)

    @classmethod
    def add(cls, provider_cls: type[BaseProviderClient]) -> None:
        """Register a provider (e.g. MockProvider)."""
        cls._current[provider_cls.PROVIDER_CODE] = provider_cls

    @classmethod
    def reset(cls) -> None:
        """Restore default provider set."""
        cls._current.clear()
        cls._current.update(cls._default)


class LLMProvider:
    """Provider facade; config and logger from ModuleStore on each access."""

    def set_cache_path(self, path: Path | str) -> None:
        """Update cache path in module config; cache reads it on each use."""
        llm_providers_set_cache_path(Path(path).resolve())

    def get_chat_request_cache(self, request: LLMChatRequest) -> LLMChatResponse | None:
        """Return cached response or None if cache disabled or miss."""
        return LLMChatRequestCache.get(request)

    def save_chat_request_cache(
        self, request: LLMChatRequest, response: LLMChatResponse
    ) -> None:
        """Save response to cache (no-op if cache path not set)."""
        LLMChatRequestCache.set(request, response)

    def _provider_codes_registered(self) -> list[str]:
        """All registered provider codes (internal)."""
        return LLMProviderStore.provider_codes()

    def provider_codes(self) -> list[str]:
        """Provider codes enabled in config (with API key where required)."""
        params = ModuleStore.get()
        return [
            code for code in self._provider_codes_registered()
            if params.providers.is_provider_available(code)
        ]

    def get_provider(self, provider_code: str) -> BaseProviderClient:
        params = ModuleStore.get()
        provider_cls = LLMProviderStore.get_class(provider_code)
        if provider_cls is None:
            raise LLMProviderDisabledError(
                f"Unknown provider '{provider_code}'"
            )
        if not params.providers.is_provider_available(provider_code):
            raise LLMProviderDisabledError(
                f"Provider '{provider_code}' is disabled or has no API key set"
            )
        return provider_cls(
            config=params.providers,
            response_logger=params.response_logger,
        )

    def models(self, request: LLMModelsRequest) -> LLMModelsResponse:
        params = ModuleStore.get()
        provider_code = request.provider or ""
        if not provider_code:
            raise LLMProviderDisabledError("Provider code is not specified")
        if not params.providers.is_provider_available(provider_code):
            raise LLMProviderDisabledError(
                f"Provider '{provider_code}' is disabled or has no API key set"
            )
        provider = self.get_provider(provider_code)
        return provider.models(request)

    def chat(self, request: LLMChatRequest, *, cache: bool = False) -> LLMChatResponse:
        provider_code = request.provider or ""
        if not provider_code:
            raise LLMProviderDisabledError("Provider code is not specified")
        provider = self.get_provider(provider_code)

        if LLMChatRequestCache.is_cache_available():
            if cache:
                cached = self.get_chat_request_cache(request)
                if cached is not None:
                    return cached
            result = provider.chat(request, cache=False)
            to_store = replace(result, cache=False)
            self.save_chat_request_cache(request, to_store)
            return result

        return provider.chat(request, cache=cache)
