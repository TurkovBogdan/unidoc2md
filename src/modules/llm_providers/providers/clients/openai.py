"""OpenAI provider — model listing and chat completion with vision support."""

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
    LLMChatReasoningEffort,
    LLMChatRequest,
    LLMChatResponse,
    LLMChatRole,
)
from ...schemas.models import LLMModelInfo, LLMModelsRequest, LLMModelsResponse


class OpenAIProvider(BaseProviderClient):
    PROVIDER_CODE = "openai"
    BASE_URL = "https://api.openai.com"
    RESPONSES_ENDPOINT = "/v1/responses"
    ROLE_MAP = {
        LLMChatRole.SYSTEM: LLMChatRole.SYSTEM.value,
        LLMChatRole.USER: LLMChatRole.USER.value,
        LLMChatRole.ASSISTANT: LLMChatRole.ASSISTANT.value,
    }
    REASONING_EFFORT_MAP = {
        LLMChatReasoningEffort.LOW: "low",
        LLMChatReasoningEffort.MEDIUM: "medium",
        LLMChatReasoningEffort.HIGH: "high",
    }
    FINISH_REASON_MAP = {
        LLM_CHAT_FINISH_STOP: LLM_CHAT_FINISH_STOP,
        LLM_CHAT_FINISH_LENGTH: LLM_CHAT_FINISH_LENGTH,
        LLM_CHAT_FINISH_CONTENT_FILTER: LLM_CHAT_FINISH_CONTENT_FILTER,
    }

    def _build_headers(self) -> dict[str, str]:
        key = (self._config.openai_api_key or "").strip()
        return {"Authorization": f"Bearer {key}"}

    def parse_error_message(self, status_code: int, body_raw: str) -> str | None:
        # OpenAI: {"error": {"message": "...", "type": "invalid_request_error", "code": "invalid_api_key", "param": null}}
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
            code = (err.get("code") or err.get("type") or "").strip()
            return code or None
        err_code = (err.get("code") or err.get("type") or "").strip()
        if err_code:
            return f"{err_code}: {msg}"
        return msg

    def _fetch_models(self) -> list[dict]:
        if not (self._config.openai_api_key or "").strip():
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

    def chat(self, request: LLMChatRequest, *, cache: bool = False) -> LLMChatResponse:
        """Send chat request to OpenAI Responses API."""
        input_data = self._build_input(request)
        reasoning_effort = self._map_reasoning_effort(request.reasoning)
        is_reasoning = reasoning_effort is not None

        body: dict = {
            "model": request.model,
            "input": input_data,
            "stream": False,
        }
        if is_reasoning:
            body["reasoning"] = {
                "effort": reasoning_effort,
                "summary": "detailed",
            }
            if request.max_tokens is not None:
                body["max_output_tokens"] = request.max_tokens
        else:
            if request.max_tokens is not None:
                body["max_output_tokens"] = request.max_tokens
            if request.temperature is not None and request.temperature != 1.0:
                body["temperature"] = request.temperature
            if request.top_p is not None:
                body["top_p"] = request.top_p

        try:
            data = self._send_post_request(
                self.RESPONSES_ENDPOINT, body, endpoint_name="responses"
            )
        except LLMProviderResponseError as e:
            if "Unsupported parameter: 'temperature'" in str(e):
                raise LLMProviderResponseError(
                    'Выбранная модель не поддерживает параметр "Температура", выставите его значение в 1.0',
                    cause=e,
                ) from e
            raise
        return self._parse_responses_response(data)

    def _build_input(self, request: LLMChatRequest) -> list[dict]:
        """Convert internal LLMChatMessage list to OpenAI Responses API input format."""
        result: list[dict] = []
        for msg in request.messages:
            role = self._map_role(msg.role)

            if len(msg.content) == 1 and isinstance(msg.content[0], LLMChatMessageText):
                result.append({"role": role, "content": msg.content[0].message})
                continue

            parts: list[dict] = []
            for block in msg.content:
                if isinstance(block, LLMChatMessageText):
                    parts.append({"type": "input_text", "text": block.message})
                elif isinstance(block, LLMChatMessageImage):
                    data_url = f"data:{block.mime};base64,{block.base64}"
                    parts.append({
                        "type": "input_image",
                        "image_url": data_url,
                    })
            result.append({"role": role, "content": parts})
        return result

    def _parse_responses_response(self, data: dict) -> LLMChatResponse:
        """Parse OpenAI Responses API response into LLMChatResponse."""
        output_items = data.get("output") or []
        if not isinstance(output_items, list) or not output_items:
            raise self._map_exception(
                ValueError("empty output in response"),
                f"OpenAI returned no output items: {data}",
            )

        content_parts: list[str] = []
        reasoning_text = ""

        for item in output_items:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "reasoning":
                summary_list = item.get("summary") or []
                if isinstance(summary_list, list):
                    summary_texts = [
                        part.get("text", "")
                        for part in summary_list
                        if isinstance(part, dict) and part.get("text")
                    ]
                    if summary_texts:
                        reasoning_text = "".join(summary_texts)
            elif item.get("type") == "message":
                for block in (item.get("content") or []):
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") in ("output_text", "text"):
                        content_parts.append(block.get("text", ""))

        full_content = "".join(content_parts)
        finish_reason = self._normalize_finish_reason(
            data.get("finish_reason") or data.get("status") or "stop"
        )

        response_message = LLMChatMessage(
            role=LLMChatRole.ASSISTANT,
            content=[LLMChatMessageText(message=full_content)],
        )

        usage = data.get("usage") or {}
        output_details = usage.get("output_tokens_details") or {}
        reasoning_tokens = output_details.get("reasoning_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        tokens_usage = self._create_tokens_usage(
            prompt=usage.get("input_tokens", 0),
            reasoning=reasoning_tokens,
            completion=max(0, output_tokens - reasoning_tokens),
            total=usage.get("total_tokens", 0),
        )

        return LLMChatResponse(
            response_id=data.get("id"),
            message=response_message,
            finish_reason=finish_reason,
            created=data.get("created_at") or data.get("created", 0),
            tokens_usage=tokens_usage,
            message_reasoning=reasoning_text,
        )
