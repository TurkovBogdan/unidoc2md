"""LM Studio — локальный OpenAI-совместимый сервер (/v1/models, /v1/chat/completions)."""

from __future__ import annotations

import json

from ...errors import LLMProviderResponseError
from ...interfaces.provider_client import BaseProviderClient
from ...schemas.chat import (
    LLM_CHAT_FINISH_CONTENT_FILTER,
    LLM_CHAT_FINISH_LENGTH,
    LLM_CHAT_FINISH_STOP,
    LLMChatMessage,
    LLMChatMessageImage,
    LLMChatMessageText,
    LLMChatRequest,
    LLMChatResponse,
    LLMChatRole,
)
from ...schemas.models import LLMModelInfo, LLMModelsRequest, LLMModelsResponse


def _format_host_for_url(host: str) -> str:
    h = (host or "").strip()
    if ":" in h and not h.startswith("["):
        return f"[{h}]"
    return h


class LMStudioProvider(BaseProviderClient):
    PROVIDER_CODE = "lmstudio"
    BASE_URL = ""
    ROLE_MAP = {
        LLMChatRole.SYSTEM: LLMChatRole.SYSTEM.value,
        LLMChatRole.USER: LLMChatRole.USER.value,
        LLMChatRole.ASSISTANT: LLMChatRole.ASSISTANT.value,
    }
    FINISH_REASON_MAP = {
        LLM_CHAT_FINISH_STOP: LLM_CHAT_FINISH_STOP,
        LLM_CHAT_FINISH_LENGTH: LLM_CHAT_FINISH_LENGTH,
        LLM_CHAT_FINISH_CONTENT_FILTER: LLM_CHAT_FINISH_CONTENT_FILTER,
        "stop": LLM_CHAT_FINISH_STOP,
        "length": LLM_CHAT_FINISH_LENGTH,
        "content_filter": LLM_CHAT_FINISH_CONTENT_FILTER,
    }

    def _request_base_url(self) -> str:
        host = _format_host_for_url((self._config.lmstudio_host or "").strip())
        port = int((self._config.lmstudio_port or "").strip())
        scheme = "https" if self._config.lmstudio_ssl else "http"
        return f"{scheme}://{host}:{port}".rstrip("/")

    def _build_headers(self) -> dict[str, str]:
        key = (self._config.lmstudio_api_key or "").strip()
        if key:
            return {"Authorization": f"Bearer {key}"}
        return {}

    def parse_error_message(self, status_code: int, body_raw: str) -> str | None:
        try:
            data = json.loads(body_raw) if body_raw.strip() else {}
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(data, dict):
            return None
        err = data.get("error")
        if isinstance(err, dict):
            msg = (err.get("message") or "").strip()
            if not msg:
                code = (err.get("code") or err.get("type") or "").strip()
                return code or None
            err_code = (err.get("code") or err.get("type") or "").strip()
            return f"{err_code}: {msg}" if err_code else msg
        if isinstance(err, str) and err.strip():
            return err.strip()
        return None

    def _fetch_models(self) -> list[dict]:
        data = self._send_get_request("/v1/models")
        raw = data.get("data") if isinstance(data, dict) else None
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    def models(self, request: LLMModelsRequest) -> LLMModelsResponse:
        result: list[LLMModelInfo] = []
        for item in self._fetch_models():
            mid = (item.get("id") or "").strip()
            if not mid:
                continue
            created = item.get("created")
            if not isinstance(created, (int, float)):
                created = 0
            result.append(
                LLMModelInfo(
                    provider=self.provider_code,
                    model=mid,
                    created=int(created),
                )
            )
        return LLMModelsResponse(provider=self.provider_code, models=tuple(result))

    def _build_message_content(
        self, content: list[LLMChatMessageText | LLMChatMessageImage]
    ) -> str | list[dict]:
        if all(isinstance(c, LLMChatMessageText) for c in content):
            return "".join(c.message for c in content)
        parts: list[dict] = []
        for item in content:
            if isinstance(item, LLMChatMessageText):
                parts.append({"type": "text", "text": item.message})
            elif isinstance(item, LLMChatMessageImage):
                parts.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{item.mime};base64,{item.base64}",
                        },
                    }
                )
        return parts

    def _serialize_messages(self, messages: list[LLMChatMessage]) -> list[dict]:
        return [
            {
                "role": self._map_role(msg.role),
                "content": self._build_message_content(msg.content),
            }
            for msg in messages
        ]

    def _parse_chat_response(self, data: dict) -> LLMChatResponse:
        choices = data.get("choices") or []
        if not choices:
            raise LLMProviderResponseError(
                f"LM Studio response contains no choices; raw: {self._serialize_log_body(data)}"
            )
        choice = choices[0] if isinstance(choices[0], dict) else {}
        raw_msg = choice.get("message") or {}
        if not isinstance(raw_msg, dict):
            raw_msg = {}
        content_raw = raw_msg.get("content")
        if isinstance(content_raw, str):
            content_str = content_raw
        elif isinstance(content_raw, list):
            parts: list[str] = []
            for part in content_raw:
                if isinstance(part, dict) and part.get("type") == "text":
                    parts.append(str(part.get("text", "")))
            content_str = "".join(parts)
        else:
            content_str = str(content_raw or "")

        finish_reason = self._normalize_finish_reason(choice.get("finish_reason"))

        message = LLMChatMessage(
            role=LLMChatRole.ASSISTANT,
            content=[LLMChatMessageText(message=content_str)],
        )

        raw_usage = data.get("usage")
        tokens_usage = None
        if isinstance(raw_usage, dict):
            tokens_usage = self._create_tokens_usage(
                prompt=raw_usage.get("prompt_tokens", 0),
                reasoning=0,
                completion=raw_usage.get("completion_tokens", 0),
                total=raw_usage.get("total_tokens", 0),
            )

        return LLMChatResponse(
            response_id=data.get("id"),
            message=message,
            finish_reason=finish_reason,
            created=int(data.get("created", 0) or 0),
            tokens_usage=tokens_usage,
            message_reasoning="",
        )

    def chat(self, request: LLMChatRequest, *, cache: bool = False) -> LLMChatResponse:
        body: dict = {
            "model": request.model,
            "messages": self._serialize_messages(request.messages),
            "stream": False,
        }
        if request.max_tokens is not None:
            body["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            body["temperature"] = request.temperature
        if request.top_p is not None:
            body["top_p"] = request.top_p

        data = self._send_post_request(
            "/v1/chat/completions",
            body,
            endpoint_name="chat/completions",
        )
        return self._parse_chat_response(data)
