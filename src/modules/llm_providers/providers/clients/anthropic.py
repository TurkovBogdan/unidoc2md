"""Anthropic provider — chat completion with vision support."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

from ...interfaces.provider_client import BaseProviderClient
from ...schemas.chat import (
    LLM_CHAT_FINISH_CONTENT_FILTER,
    LLM_CHAT_FINISH_LENGTH,
    LLM_CHAT_FINISH_STOP,
    LLMChatMessage,
    LLMChatMessageImage,
    LLMChatMessageText,
    LLMChatReasoningEffort,
    LLMChatRequest,
    LLMChatResponse,
    LLMChatRole,
)
from ...schemas.models import LLMModelInfo, LLMModelsRequest, LLMModelsResponse


def _parse_created(value: str | int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    s = (value or "").strip()
    if not s:
        return 0
    try:
        s = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return 0


def _build_content_block(item: LLMChatMessageText | LLMChatMessageImage) -> dict:
    """Convert message content block → Anthropic API content block."""
    if isinstance(item, LLMChatMessageText):
        return {"type": "text", "text": item.message}
    # LLMChatMessageImage
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": item.mime,
            "data": item.base64,
        },
    }


class AnthropicProvider(BaseProviderClient):
    PROVIDER_CODE = "anthropic"
    BASE_URL = "https://api.anthropic.com"
    ROLE_MAP = {
        LLMChatRole.SYSTEM: LLMChatRole.SYSTEM.value,
        LLMChatRole.USER: LLMChatRole.USER.value,
        LLMChatRole.ASSISTANT: LLMChatRole.ASSISTANT.value,
    }
    THINKING_BUDGET_MAP = {
        LLMChatReasoningEffort.LOW: 1024,
        LLMChatReasoningEffort.MEDIUM: 8000,
        LLMChatReasoningEffort.HIGH: 16000,
    }
    FINISH_REASON_MAP = {
        "end_turn": LLM_CHAT_FINISH_STOP,
        "max_tokens": LLM_CHAT_FINISH_LENGTH,
        "stop_sequence": LLM_CHAT_FINISH_STOP,
        "tool_use": LLM_CHAT_FINISH_STOP,
        "content_filter": LLM_CHAT_FINISH_CONTENT_FILTER,
    }

    def _build_headers(self) -> dict[str, str]:
        key = (self._config.anthropic_api_key or "").strip()
        return {
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        }

    def parse_error_message(self, status_code: int, body_raw: str) -> str | None:
        # Anthropic: {"type": "error", "error": {"type": "authentication_error", "message": "invalid x-api-key"}, "request_id": "..."}
        try:
            data = json.loads(body_raw) if body_raw.strip() else {}
        except (json.JSONDecodeError, TypeError):
            return None
        if not isinstance(data, dict):
            return None
        err = data.get("error")
        if not isinstance(err, dict):
            return None
        msg = (err.get("message") or "").strip()
        if not msg:
            return None
        err_type = (err.get("type") or "").strip()
        if err_type:
            return f"{err_type}: {msg}"
        return msg

    def _fetch_models(self) -> list[dict]:
        if not (self._config.anthropic_api_key or "").strip():
            return []
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
            result.append(
                LLMModelInfo(
                    provider=self.provider_code,
                    model=mid,
                    created=_parse_created(item.get("created_at")),
                )
            )
        return LLMModelsResponse(provider=self.provider_code, models=tuple(result))

    def _build_messages_payload(
        self,
        messages: list[LLMChatMessage],
    ) -> tuple[str | None, list[dict]]:
        """
        Split messages into (system_prompt, api_messages).

        Anthropic API требует system как отдельный параметр верхнего уровня.
        Если system-сообщений несколько — конкатенируем через \n\n.

        Thinking-блоки из предыдущих ответов ассистента в LLMChatMessage не попадают:
        content только LLMChatMessageText | LLMChatMessageImage, поэтому в multi-turn
        thinking не переотправляется — корректно.
        """
        system_parts: list[str] = []
        api_messages: list[dict] = []

        for msg in messages:
            if msg.role == LLMChatRole.SYSTEM:
                for item in msg.content:
                    if isinstance(item, LLMChatMessageText):
                        system_parts.append(item.message)
                continue

            api_messages.append({
                "role": self._map_role(msg.role),
                "content": [_build_content_block(item) for item in msg.content],
            })

        system_prompt = "\n\n".join(system_parts) if system_parts else None
        return system_prompt, api_messages

    def chat(self, request: LLMChatRequest, *, cache: bool = False) -> LLMChatResponse:
        system_prompt, api_messages = self._build_messages_payload(request.messages)

        body: dict = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": api_messages,
        }
        if system_prompt is not None:
            body["system"] = system_prompt

        thinking_budget = self._map_thinking_budget(request.reasoning)
        if thinking_budget is not None:
            # Минимум 1024 по документации Anthropic; при thinking API требует temperature=1
            body["thinking"] = {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }
            body["temperature"] = 1
        else:
            if request.temperature is not None:
                body["temperature"] = request.temperature
            if request.top_p is not None:
                body["top_p"] = request.top_p

        data = self._send_post_request(
            "/v1/messages",
            body,
            endpoint_name="chat",
        )

        content_blocks: list[dict] = data.get("content") or []
        thinking_parts = [
            block["thinking"]
            for block in content_blocks
            if block.get("type") == "thinking" and "thinking" in block
        ]
        text_parts = [
            block["text"]
            for block in content_blocks
            if block.get("type") == "text" and "text" in block
        ]
        reply_text = "\n".join(text_parts)
        reasoning_text = "\n".join(thinking_parts).strip() or None

        usage_raw: dict = data.get("usage") or {}
        # total_tokens не приходит в ответе Anthropic — считаем вручную
        tokens_usage = self._create_tokens_usage(
            prompt=usage_raw.get("input_tokens", 0),
            reasoning=0,  # output_tokens включает thinking, отдельного поля нет
            completion=usage_raw.get("output_tokens", 0),
            total=usage_raw.get("input_tokens", 0) + usage_raw.get("output_tokens", 0),
        )

        finish_reason = self._normalize_finish_reason(data.get("stop_reason"))

        return LLMChatResponse(
            response_id=data.get("id"),
            message=LLMChatMessage(
                role=LLMChatRole.ASSISTANT,
                content=[LLMChatMessageText(message=reply_text)],
            ),
            finish_reason=finish_reason,
            created=int(time.time()),
            tokens_usage=tokens_usage,
            message_reasoning=reasoning_text or "",
        )
