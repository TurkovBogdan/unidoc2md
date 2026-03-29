"""Registry store tests: load from file, save to file."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.modules.llm_models_registry.providers.llm_model_store import LLMModelStore

REGISTRY_FILENAME = "llm_models_registry.json"


def test_load_missing_file_data_empty(tmp_path: Path) -> None:
    """When the file is missing, after load() store.data == {}."""
    store = LLMModelStore(store_file_path=tmp_path / REGISTRY_FILENAME)
    store.load()
    assert store.data == {}


def test_load_legacy_json_array_ignored(tmp_path: Path) -> None:
    """Legacy JSON list format is unsupported: load yields empty store.data."""
    path = tmp_path / REGISTRY_FILENAME
    payload = [
        {"provider": "openai", "name": "gpt-4", "enabled": True},
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    store = LLMModelStore(store_file_path=path)
    store.load()
    assert store.data == {}
    persisted = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(persisted, list)


def test_load_valid_json_object_fills_data(tmp_path: Path) -> None:
    """Valid JSON object is loaded as-is into store.data."""
    path = tmp_path / REGISTRY_FILENAME
    payload = {
        "openai@gpt-4": {"provider": "openai", "name": "gpt-4", "enabled": True},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    store = LLMModelStore(store_file_path=path)
    store.load()
    assert len(store.data) == 1
    assert "openai@gpt-4" in store.data


def test_load_invalid_json_data_empty(tmp_path: Path) -> None:
    """Invalid JSON leaves store.data == {} after load()."""
    path = tmp_path / REGISTRY_FILENAME
    path.write_text("{ invalid", encoding="utf-8")
    store = LLMModelStore(store_file_path=path)
    store.load()
    assert store.data == {}


def test_save_creates_file_and_content_matches(tmp_path: Path) -> None:
    """save() creates the file; on-disk content matches store.data."""
    path = tmp_path / REGISTRY_FILENAME
    store = LLMModelStore(store_file_path=path)
    store.data = {
        "test@model-1": {"provider": "test", "name": "model-1", "enabled": True},
    }
    store.save()
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == store.data
    assert data["test@model-1"]["provider"] == "test"
    assert data["test@model-1"]["name"] == "model-1"


def test_save_creates_directory_if_needed(tmp_path: Path) -> None:
    """save() creates parent directories when needed."""
    subdir = tmp_path / "sub" / "dir"
    store = LLMModelStore(store_file_path=subdir / REGISTRY_FILENAME)
    store.data = {}
    store.save()
    assert (subdir / REGISTRY_FILENAME).exists()
