"""Load and save the model registry JSON file. Single source of truth: store.data."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..module import ModuleConfigStore


class LLMModelStore:
    """
    Registry storage: one `data` dict (key → record), key = provider@name.
    Default file path comes from ModuleConfigStore (models_store_file).
    An alternate path may be passed to the constructor.
    """

    def __init__(self, store_file_path: Path | str | None = None) -> None:
        if store_file_path is not None:
            self.store_file_path = Path(store_file_path).resolve()
        else:
            self.store_file_path = ModuleConfigStore.get().models_store_file
        self.data: dict[str, dict] = {}

    @staticmethod
    def _serialize_value(obj: object) -> object:
        """Recursively coerce values to JSON-serializable form (datetime → ISO string)."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: LLMModelStore._serialize_value(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [LLMModelStore._serialize_value(v) for v in obj]
        return obj

    @staticmethod
    def _record_key(item: dict) -> str | None:
        """Record key: provider@name. None if provider or name is empty."""
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
        """Read store_file_path into self.data."""
        path = self.store_file_path
        try:
            if not path.exists():
                self.data = {}
                return
            raw = path.read_text(encoding="utf-8").strip()
            parsed = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, OSError):
            self.data = {}
            return

        if isinstance(parsed, dict):
            normalized: dict[str, dict] = {}
            for key, item in parsed.items():
                if not isinstance(item, dict):
                    continue
                item_key = self._record_key(item)
                use_key = item_key or str(key).strip()
                if not use_key:
                    continue
                normalized[use_key] = item
            self.data = normalized
            return

        self.data = {}

    def save(self) -> None:
        """Write self.data to store_file_path; create parent directories if needed."""
        path = self.store_file_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._serialize_value(self.data)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


__all__ = ["LLMModelStore"]
