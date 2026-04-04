"""Base abstract contract for an LLM provider client."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from ..module import LLMProvidersConfig, ModuleStore
from ..errors import (
    LLMProviderAuthError,
    LLMProviderClientError,
    LLMProviderRateLimitError,
    LLMProviderResponseError,
    LLMProviderTransportError,
)
from .response_logger import ResponseLoggerProtocol
from ..schemas.chat import (
    LLM_CHAT_FINISH_STOP,
    LLMChatReasoningEffort,
    LLMChatRequest,
    LLMChatResponse,
    LLMChatRole,
    LLMChatTokensUsage,
)
from ..schemas.models import LLMModelInfo, LLMModelsRequest, LLMModelsResponse

RAW_RESPONSE_MAX_CHARS = 4096


def _read_error_body(err: urllib.error.HTTPError) -> str:
    try:
        return err.read().decode("utf-8", errors="replace").strip() or "(empty)"
    except Exception:
        return "(failed to read body)"


def _build_url(base_url: str, endpoint: str) -> str:
    """Build a full URL from a base URL and endpoint path."""
    base = (base_url or "").rstrip("/")
    path = (endpoint or "").strip("/")
    return f"{base}/{path}" if base and path else (base or f"/{path}")


class BaseProviderClient(ABC):
    """
    Base class for model provider API clients.
    Subclasses define `BASE_URL` and implement `models(LLMModelsRequest) -> LLMModelsResponse`.
    Request sending, raw response recording, and error mapping are handled here.
    """

    PROVIDER_CODE: str = ""
    BASE_URL: str = ""
    ROLE_MAP: dict[LLMChatRole, str] = {}
    REASONING_EFFORT_MAP: dict[LLMChatReasoningEffort, str] = {}
    THINKING_BUDGET_MAP: dict[LLMChatReasoningEffort, int] = {}
    FINISH_REASON_MAP: dict[str, str] = {}

    def __init__(
        self,
        config: LLMProvidersConfig,
        response_logger: ResponseLoggerProtocol | None = None,
    ) -> None:
        self._config = config
        self._response_logger = (
            ModuleStore.get().response_logger if response_logger is None else response_logger
        )
        self._headers = self._build_headers()
        self._connect_timeout: float = float(config.gateway_connect_timeout or 60)
        self._read_timeout: float = float(config.gateway_read_timeout or 600)

    def _apply_read_timeout(self, response: Any) -> None:
        """
        Apply read timeout to an opened urllib response socket.
        urllib exposes only one timeout in urlopen(); we set connect timeout at open(),
        then switch socket timeout to read timeout before reading the body.
        """
        try:
            sock = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
            if sock is not None and hasattr(sock, "settimeout"):
                sock.settimeout(self._read_timeout)
        except Exception:
            # Best-effort: keep request flow working even if socket internals differ.
            return

    def _request_base_url(self) -> str:
        """Base URL for HTTP requests; override when URL comes from config (e.g. local LM Studio)."""
        return (self.__class__.BASE_URL or "").rstrip("/")

    @property
    def provider_code(self) -> str:
        """Provider code such as `anthropic`, `openai`, or `mock`."""
        return self.__class__.PROVIDER_CODE

    @abstractmethod
    def _build_headers(self) -> dict[str, str]:
        """Build request headers from provider config."""
        ...

    @abstractmethod
    def models(self, request: LLMModelsRequest) -> LLMModelsResponse:
        """
        Return available models for this provider (public API).
        No caching.
        """
        ...

    @abstractmethod
    def chat(self, request: LLMChatRequest, *, cache: bool = False) -> LLMChatResponse:
        """
        Send chat completion request. If cache=True, result may be served from cache.
        """
        ...

    @abstractmethod
    def parse_error_message(self, status_code: int, body_raw: str) -> str | None:
        """
        Извлечь сообщение об ошибке из тела ответа API.
        Возвращает None, чтобы использовать штатное сообщение (код, reason, body).
        """
        ...

    def _serialize_log_body(
        self,
        body: Any,
    ) -> str:
        """Convert a response or error payload to a compact log string."""
        try:
            raw = json.dumps(body, ensure_ascii=False)
        except (TypeError, ValueError):
            raw = str(body)
        if len(raw) > RAW_RESPONSE_MAX_CHARS:
            raw = raw[:RAW_RESPONSE_MAX_CHARS] + "..."
        return raw

    def _log_raw_response(
        self,
        endpoint: str,
        body: Any,
        *,
        status: int | None = None,
        is_error: bool = False,
        error_type: str | None = None,
    ) -> None:
        """Передать сырой ответ API в ResponseLoggerProtocol.debug(), если логгер передан."""
        if self._response_logger is None:
            return
        kind = "error" if is_error else "response"
        err_label = (error_type or "-") if is_error else "-"
        status_str = str(status) if status is not None else "-"
        self._response_logger.debug(
            "gateway api | provider=%s endpoint=%s status=%s kind=%s error_type=%s | %s",
            self.provider_code,
            endpoint,
            status_str,
            kind,
            err_label,
            self._serialize_log_body(body),
        )

    def _map_exception(
        self,
        e: Exception,
        message: str | None = None,
    ) -> LLMProviderClientError:
        """Map a low-level exception to a typed provider client error."""
        msg = message if message is not None else str(e)
        if isinstance(e, urllib.error.HTTPError):
            if e.code in (401, 403):
                return LLMProviderAuthError(msg, cause=e)
            if e.code == 429:
                return LLMProviderRateLimitError(msg, cause=e)
            return LLMProviderResponseError(msg, cause=e)
        if isinstance(e, (urllib.error.URLError, OSError, TimeoutError)):
            return LLMProviderTransportError(msg, cause=e)
        if isinstance(e, json.JSONDecodeError):
            return LLMProviderResponseError(msg, cause=e)
        return LLMProviderResponseError(msg, cause=e)

    def _create_tokens_usage(
        self,
        *,
        prompt: int = 0,
        completion: int = 0,
        total: int = 0,
        reasoning: int = 0,
    ) -> LLMChatTokensUsage:
        """Create a normalized LLMChatTokensUsage object with zero defaults."""
        return LLMChatTokensUsage(
            prompt=prompt,
            reasoning=reasoning,
            completion=completion,
            total=total,
        )

    def _map_role(self, role: LLMChatRole) -> str:
        """Map normalized chat role to provider-specific role string."""
        return self.__class__.ROLE_MAP.get(role, role.value)

    def _map_reasoning_effort(
        self,
        reasoning: LLMChatReasoningEffort,
    ) -> str | None:
        """Map normalized reasoning effort to provider-specific value."""
        if reasoning == LLMChatReasoningEffort.DISABLED:
            return None
        return self.__class__.REASONING_EFFORT_MAP.get(reasoning)

    def _map_thinking_budget(
        self,
        reasoning: LLMChatReasoningEffort,
        *,
        disabled_budget: int | None = None,
    ) -> int | None:
        """Map normalized reasoning effort to provider-specific token budget."""
        if reasoning == LLMChatReasoningEffort.DISABLED:
            return disabled_budget
        return self.__class__.THINKING_BUDGET_MAP.get(reasoning)

    def _normalize_finish_reason(self, raw_reason: str | None) -> str:
        """Normalize provider finish reason to the shared response schema."""
        if not raw_reason:
            return LLM_CHAT_FINISH_STOP
        return self.__class__.FINISH_REASON_MAP.get(raw_reason, LLM_CHAT_FINISH_STOP)

    def _send_request(
        self,
        method: str,
        endpoint: str,
        *,
        body: Any = None,
        endpoint_name: str | None = None,
    ) -> Any:
        """
        Send an HTTP request and return parsed JSON.
        Uses `self._headers` built in the constructor.
        `endpoint` is relative to `BASE_URL`, for example `/v1/models`.
        `body` is sent as JSON for POST requests and ignored for GET requests.
        `endpoint_name` is an optional label for logs.
        """
        url = _build_url(self._request_base_url(), endpoint)
        log_label = endpoint_name if endpoint_name is not None else endpoint
        merged_headers = {
            "Accept": "application/json",
            "User-Agent": "unidoc2md/1.0",
            **self._headers,
        }
        if method.upper() == "POST" and body is not None:
            merged_headers["Content-Type"] = "application/json"
            payload = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers=merged_headers, method="POST")
        else:
            req = urllib.request.Request(url, headers=merged_headers, method=method.upper())
        ctx = ssl.create_default_context()
        try:
            with urllib.request.urlopen(
                req, timeout=self._connect_timeout, context=ctx
            ) as resp:
                self._apply_read_timeout(resp)
                raw_body = resp.read().decode("utf-8")
                status_code = resp.getcode()
            data = json.loads(raw_body) if raw_body else {}
        except urllib.error.HTTPError as e:
            body_msg = _read_error_body(e)
            parsed_msg = self.parse_error_message(e.code, body_msg)
            msg = (
                parsed_msg
                if parsed_msg is not None
                else f"{e.code} {e.reason or e.msg}; body: {body_msg}"
            )
            self._log_raw_response(
                log_label, msg, status=e.code, is_error=True, error_type=type(e).__name__
            )
            raise self._map_exception(e, msg) from e
        except Exception as e:
            msg = str(e)
            self._log_raw_response(log_label, msg, is_error=True, error_type=type(e).__name__)
            raise self._map_exception(e, msg) from e
        self._log_raw_response(log_label, data, status=status_code)
        return data

    def _send_get_request(
        self,
        endpoint: str,
        *,
        endpoint_name: str | None = None,
    ) -> Any:
        """Send a GET request and return parsed JSON."""
        return self._send_request("GET", endpoint, endpoint_name=endpoint_name)

    def _send_post_request(
        self,
        endpoint: str,
        body: Any,
        *,
        endpoint_name: str | None = None,
    ) -> Any:
        """Send a POST request with JSON body and return parsed JSON."""
        return self._send_request(
            "POST", endpoint, body=body, endpoint_name=endpoint_name
        )
