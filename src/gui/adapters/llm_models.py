"""GUI adapters for the LLM model registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from src.modules.llm_models_registry import (
    LLMModelManager,
    SyncModelRegistryService,
)


@dataclass
class SyncReport:
    """Sync result summary for the GUI."""

    providers_count: int = 0
    models_total: int = 0
    models_new: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class LLMProviderModelRecord:
    """GUI view of a single registry model record."""

    provider_code: str
    code: str
    can_update: bool = False
    enabled: bool = True
    input_text: bool = False
    input_image: bool = False
    input_audio: bool = False
    input_video: bool = False
    output_text: bool = False
    output_image: bool = False
    output_audio: bool = False
    output_video: bool = False
    chat: bool = False
    function_calling: bool = False
    structured_output: bool = False
    reasoning: bool = False
    context_window: int | None = None
    price_input: float | None = None
    price_output: float | None = None
    created: int | None = None

    @property
    def model_key(self) -> str:
        return f"{self.provider_code}@{self.code}"

    @classmethod
    def from_record(cls, record: dict) -> "LLMProviderModelRecord":
        return cls(
            provider_code=(record.get("provider") or record.get("provider_code") or "").strip(),
            code=(record.get("name") or record.get("code") or "").strip(),
            can_update=bool(record.get("can_update", False)),
            enabled=bool(record.get("enabled", True)),
            input_text=bool(record.get("input_text") or record.get("text_support", False)),
            input_image=bool(record.get("input_image") or record.get("image_support", False)),
            input_audio=bool(record.get("input_audio", False)),
            input_video=bool(record.get("input_video", False)),
            output_text=bool(record.get("output_text", False)),
            output_image=bool(record.get("output_image", False)),
            output_audio=bool(record.get("output_audio", False)),
            output_video=bool(record.get("output_video", False)),
            chat=bool(record.get("chat", False)),
            function_calling=bool(record.get("function_calling", False)),
            structured_output=bool(record.get("structured_output", False)),
            reasoning=bool(record.get("reasoning", False)),
            context_window=record.get("context_window"),
            price_input=record.get("price_input"),
            price_output=record.get("price_output"),
            created=record.get("created"),
        )


def _is_provider_enabled(provider_code: str) -> bool:
    from src.core import AppConfigStore

    return AppConfigStore.get().llm_providers.is_provider_enabled(provider_code)


class LLMModelsAdapter:
    """GUI bridge between screens and the domain model registry manager."""

    def __init__(self, app_root: Path | None = None) -> None:
        self._app_root = app_root
        self._manager = LLMModelManager()

    def list_models(self) -> list[LLMProviderModelRecord]:
        """Models for the GUI, filtered to enabled providers."""
        records = self._manager.get_sorted_records()
        result: list[LLMProviderModelRecord] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            provider_code = (record.get("provider") or record.get("provider_code") or "").strip()
            if not provider_code or not _is_provider_enabled(provider_code):
                continue
            result.append(LLMProviderModelRecord.from_record(record))
        return result

    def get_model(self, model_key: str) -> LLMProviderModelRecord | None:
        """One registry record by ``provider@name`` key."""
        record = self._manager.get_record(model_key)
        if record is None:
            return None
        return LLMProviderModelRecord.from_record(record)

    def update_model(self, model_key: str, **fields: object) -> bool:
        """Apply a user edit and block bootstrap merge for this model."""
        return self._manager.update_user_model(model_key, **fields)

    def sync_available_models(self) -> SyncReport:
        """Sync the registry with providers for the GUI."""
        try:
            result = SyncModelRegistryService.sync_models()
            return SyncReport(
                providers_count=result.providers_count,
                models_total=result.models_total,
                models_new=result.models_new,
                errors=result.errors,
            )
        except Exception as exc:
            return SyncReport(errors=[str(exc)])


_adapters: dict[Path | None, LLMModelsAdapter] = {}


def get_llm_models_adapter(root: Path | None = None) -> LLMModelsAdapter:
    """Return a cached GUI adapter for the model registry."""
    key = Path(root).resolve() if root else None
    if key not in _adapters:
        _adapters[key] = LLMModelsAdapter(root)
    return _adapters[key]


__all__ = [
    "LLMModelsAdapter",
    "LLMProviderModelRecord",
    "SyncReport",
    "get_llm_models_adapter",
]
