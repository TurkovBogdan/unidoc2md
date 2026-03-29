"""Registry: in-memory ``data``; ``save`` writes it to the JSON file; ``load`` replaces ``data`` from that file."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..module import ModuleConfigStore

LLM_MODEL_STORE: LLMModelStore | None = None


def bind_llm_model_store() -> None:
    """Set ``LLM_MODEL_STORE`` from ``ModuleConfigStore`` path and ``load()`` (replace instance)."""
    global LLM_MODEL_STORE
    resolved = ModuleConfigStore.get().models_store_file.resolve()
    LLM_MODEL_STORE = LLMModelStore(store_file_path=resolved)
    LLM_MODEL_STORE.load()


def reset_llm_model_store() -> None:
    """Drop runtime store (tests / before rebinding)."""
    global LLM_MODEL_STORE
    LLM_MODEL_STORE = None


class LLMModelStore:
    """``data`` = ``provider@name`` → row. Runtime: module ``LLM_MODEL_STORE`` (see ``bind_llm_model_store``)."""

    def __init__(self, store_file_path: Path | str | None = None) -> None:
        if store_file_path is None:
            raise TypeError(
                "LLMModelStore() requires store_file_path=... for an isolated store; "
                "runtime uses module-level LLM_MODEL_STORE (bind_llm_model_store)."
            )
        self.store_file_path = Path(store_file_path).resolve()
        self.data: dict[str, dict] = {}

    @staticmethod
    def _read_file_into(path: Path, target: dict[str, dict]) -> None:
        target.clear()
        try:
            if not path.exists():
                return
            raw = path.read_text(encoding="utf-8").strip()
            parsed = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, OSError):
            return

        if not isinstance(parsed, dict):
            return
        for key, item in parsed.items():
            if not isinstance(item, dict):
                continue
            item_key = LLMModelStore._record_key(item)
            use_key = item_key or str(key).strip()
            if not use_key:
                continue
            target[use_key] = item

    @staticmethod
    def _serialize_value(obj: object) -> object:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: LLMModelStore._serialize_value(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [LLMModelStore._serialize_value(v) for v in obj]
        return obj

    @staticmethod
    def _record_key(item: dict) -> str | None:
        provider = item.get("provider") or item.get("provider_code")
        name = item.get("name") or item.get("code")
        if provider is None or name is None:
            return None
        p = str(provider).strip()
        n = str(name).strip()
        if not p or not n:
            return None
        return f"{p}@{n}"

    def load(self) -> None:
        self._read_file_into(self.store_file_path, self.data)

    def save(self) -> None:
        path = self.store_file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._serialize_value(self.data)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


__all__ = ["LLM_MODEL_STORE", "bind_llm_model_store", "reset_llm_model_store"]
