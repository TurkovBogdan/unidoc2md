"""Bootstrap and merge logic for the model registry file."""

from __future__ import annotations

import json
from pathlib import Path


class LLMModelStoreMerger:
    """Merge bundled registry into the user file on boot; merge from assets into user path."""

    @staticmethod
    def _to_record_map(payload: object) -> dict[str, dict]:
        """Normalize registry JSON to dict[key, record]; only object (mapping) format is supported."""
        if not isinstance(payload, dict):
            return {}
        normalized: dict[str, dict] = {}
        for key, item in payload.items():
            if not isinstance(item, dict):
                continue
            record_key = LLMModelStoreMerger._record_key(item)
            use_key = record_key or str(key).strip()
            if not use_key:
                continue
            normalized[use_key] = item
        return normalized

    @staticmethod
    def _record_key(item: dict) -> str | None:
        """Record key: provider@name."""
        provider = item.get("provider")
        name = item.get("name")
        if provider is None or name is None:
            return None
        p = str(provider).strip()
        n = str(name).strip()
        if not p or not n:
            return None
        return f"{p}@{n}"

    @staticmethod
    def _can_update_from_record(record: dict) -> bool:
        """Whether the incoming record allows overwriting an existing entry (can_update)."""
        return bool(record.get("can_update", False))

    @staticmethod
    def _apply_boot_merge(source_map: dict[str, dict], current_map: dict[str, dict]) -> bool:
        """
        Apply boot-merge rules to the current map:
        1. Model present in source but not in target — add.
        2. Model in both and target has can_update=true — overwrite target fields from source
           (service path for rows not yet pinned by the user).
        Returns True if current_map was modified.
        """
        changed = False
        for key, record in source_map.items():
            if key not in current_map:
                current_map[key] = dict(record)
                changed = True
            else:
                target_record = current_map[key]
                source_can_update = bool(record.get("can_update", False))
                target_can_update = bool(target_record.get("can_update", False))
                if not source_can_update and target_can_update:
                    for k, v in record.items():
                        current_map[key][k] = v
                    changed = True
        return changed

    @staticmethod
    def apply_boot_merge(
        source_file: Path | str,
        target_file: Path | str,
    ) -> None:
        """
        Create or update target_file from source_file (full paths to registry JSON).
        """
        source = Path(source_file).resolve()
        target = Path(target_file).resolve()

        if target.exists():
            if not source.exists():
                return
            try:
                source_map = LLMModelStoreMerger._to_record_map(
                    json.loads(source.read_text(encoding="utf-8"))
                )
            except (json.JSONDecodeError, OSError):
                return
            if not source_map:
                return
            try:
                current_map = LLMModelStoreMerger._to_record_map(
                    json.loads(target.read_text(encoding="utf-8").strip() or "{}")
                )
            except (json.JSONDecodeError, OSError):
                return
            if LLMModelStoreMerger._apply_boot_merge(source_map, current_map):
                target.write_text(
                    json.dumps(current_map, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            return

        if source.exists():
            try:
                default_models = LLMModelStoreMerger._to_record_map(
                    json.loads(source.read_text(encoding="utf-8"))
                )
            except (json.JSONDecodeError, OSError):
                default_models = {}
        else:
            default_models = {}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(default_models, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def merge_registry_from_assets(
        source_path: Path | str,
        user_path: Path | str,
        registry_filename: str,
    ) -> None:
        """
        Merge registry from source directory into the file under user_path (registry_filename).
        - If provider@name is missing — add the record.
        - If the record exists and the incoming row has can_update=true — overwrite fields.
        """
        source_dir = Path(source_path).resolve()
        user_dir = Path(user_path).resolve()
        source_file = source_dir / registry_filename
        target_file = user_dir / registry_filename
        user_dir.mkdir(parents=True, exist_ok=True)

        if not source_file.exists():
            return
        try:
            source_map = LLMModelStoreMerger._to_record_map(
                json.loads(source_file.read_text(encoding="utf-8"))
            )
        except (json.JSONDecodeError, OSError):
            return
        if not source_map:
            return

        if target_file.exists():
            try:
                current_map = LLMModelStoreMerger._to_record_map(
                    json.loads(target_file.read_text(encoding="utf-8").strip() or "{}")
                )
            except (json.JSONDecodeError, OSError):
                current_map = {}
        else:
            current_map = {}

        changed = False
        for key, record in source_map.items():
            if key not in current_map:
                current_map[key] = dict(record)
                changed = True
            elif LLMModelStoreMerger._can_update_from_record(record):
                for k, v in record.items():
                    current_map[key][k] = v
                changed = True

        if changed:
            target_file.write_text(
                json.dumps(current_map, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )


__all__ = ["LLMModelStoreMerger"]
