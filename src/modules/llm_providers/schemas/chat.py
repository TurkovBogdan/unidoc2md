from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional


# --- Контент сообщения ---

@dataclass
class LLMChatMessageText:
    """Текстовый блок внутри сообщения чата."""

    message: str


@dataclass
class LLMChatMessageImage:
    """Изображение внутри сообщения чата в base64-представлении."""

    mime: str  # image/jpeg, image/png, image/webp, image/gif
    base64: str


# --- Сообщения ---

LLM_CHAT_ROLE_SYSTEM = "system"
LLM_CHAT_ROLE_USER = "user"
LLM_CHAT_ROLE_ASSISTANT = "assistant"


class LLMChatRole(str, Enum):
    """Роль сообщения в истории диалога."""

    SYSTEM = LLM_CHAT_ROLE_SYSTEM
    USER = LLM_CHAT_ROLE_USER
    ASSISTANT = LLM_CHAT_ROLE_ASSISTANT


@dataclass
class LLMChatMessage:
    """Одно сообщение диалога с ролью и набором контент-блоков."""

    role: LLMChatRole
    content: list[LLMChatMessageText | LLMChatMessageImage]


# --- Запрос ---

LLM_CHAT_REASONING_DISABLED = "disabled"
LLM_CHAT_REASONING_LOW = "low"
LLM_CHAT_REASONING_MEDIUM = "medium"
LLM_CHAT_REASONING_HIGH = "high"


class LLMChatReasoningEffort(str, Enum):
    """Желаемый уровень reasoning для запроса к модели."""

    DISABLED = LLM_CHAT_REASONING_DISABLED
    LOW = LLM_CHAT_REASONING_LOW
    MEDIUM = LLM_CHAT_REASONING_MEDIUM
    HIGH = LLM_CHAT_REASONING_HIGH


@dataclass
class LLMChatRequest:
    """Нормализованный запрос на генерацию ответа в чате."""

    provider: str
    model: str
    messages: list[LLMChatMessage]
    top_p: Optional[float] = None
    max_tokens: int = 1024
    reasoning: LLMChatReasoningEffort = LLMChatReasoningEffort.DISABLED
    temperature: Optional[float] = 0.0  # 0.0–2.0
    stream: bool = False

    def cache_key(self) -> str:
        """Ключ кеша: MD5 от детерминированного JSON (через ChatRequestSerializer)."""
        from ..services.chat_serializer import ChatRequestSerializer
        return ChatRequestSerializer.cache_key(self)


# --- Ответ ---

LLM_CHAT_FINISH_STOP = "stop"
LLM_CHAT_FINISH_LENGTH = "length"
LLM_CHAT_FINISH_CONTENT_FILTER = "content_filter"


@dataclass
class LLMChatTokensUsage:
    """Статистика расхода токенов по запросу и ответу."""

    prompt: int
    reasoning: int
    completion: int
    total: int


@dataclass
class LLMChatResponse:
    """Нормализованный ответ чата от провайдера."""

    finish_reason: Literal[
        "stop", "length", "content_filter"
    ]  # LLM_CHAT_FINISH_STOP, LLM_CHAT_FINISH_LENGTH, LLM_CHAT_FINISH_CONTENT_FILTER
    created: int
    message: LLMChatMessage | None = None
    message_reasoning: str = ""  # extended thinking / chain-of-thought
    response_id: str | None = None
    tokens_usage: Optional[LLMChatTokensUsage] = None
    #: True — ответ отдан из файлового кеша запросов (расхода к API не было).
    cache: bool = False