"""Tests for module_llm_model_registry_boot (llm_models_registry bootstrap)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.modules.llm_models_registry.bootstrap import module_llm_model_registry_boot
from src.modules.llm_models_registry.boot import LLMModelStoreMerger

REGISTRY_FILENAME = "llm_models_registry.json"


def test_module_llm_model_registry_boot_creates_models_json(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    module_llm_model_registry_boot(
        source_llm_models_store_file=assets_dir / REGISTRY_FILENAME,
        user_llm_models_store_file=data_dir / REGISTRY_FILENAME,
    )
    path = data_dir / REGISTRY_FILENAME
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {}


def test_module_llm_model_registry_boot_idempotent(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    source_file = assets_dir / REGISTRY_FILENAME
    user_file = data_dir / REGISTRY_FILENAME
    module_llm_model_registry_boot(
        source_llm_models_store_file=source_file,
        user_llm_models_store_file=user_file,
    )
    path = data_dir / REGISTRY_FILENAME
    first_content = path.read_text()
    module_llm_model_registry_boot(
        source_llm_models_store_file=source_file,
        user_llm_models_store_file=user_file,
    )
    assert path.read_text() == first_content


def test_module_llm_model_registry_boot_does_not_touch_existing_when_no_source(tmp_path: Path) -> None:
    """If user file exists and assets has no registry, leave target unchanged."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    path = data_dir / REGISTRY_FILENAME
    existing = {
        "openai@gpt-4": {"provider": "openai", "name": "gpt-4", "enabled": True, "can_update": False},
    }
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    module_llm_model_registry_boot(
        source_llm_models_store_file=assets_dir / REGISTRY_FILENAME,
        user_llm_models_store_file=data_dir / REGISTRY_FILENAME,
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data["openai@gpt-4"]["provider"] == "openai"
    assert data["openai@gpt-4"]["name"] == "gpt-4"


def test_module_llm_model_registry_boot_copies_from_assets_when_present(tmp_path: Path) -> None:
    """If assets contains llm_model_registry.json, its content is copied to data on first create."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    assets_dir.mkdir(parents=True)
    source_file = assets_dir / REGISTRY_FILENAME
    source_file.write_text(
        json.dumps({"test@model-1": {"provider": "test", "name": "model-1"}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    module_llm_model_registry_boot(
        source_llm_models_store_file=source_file,
        user_llm_models_store_file=data_dir / REGISTRY_FILENAME,
    )
    path = data_dir / REGISTRY_FILENAME
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data["test@model-1"]["provider"] == "test"
    assert data["test@model-1"]["name"] == "model-1"


def test_module_llm_model_registry_boot_adds_missing_model_from_source(tmp_path: Path) -> None:
    """On boot: model present in source but missing in target is added."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    assets_dir.mkdir(parents=True)
    (data_dir / REGISTRY_FILENAME).write_text(
        json.dumps({"p1@m1": {"provider": "p1", "name": "m1", "enabled": True, "can_update": False}}),
        encoding="utf-8",
    )
    (assets_dir / REGISTRY_FILENAME).write_text(
        json.dumps(
            {
                "p1@m1": {"provider": "p1", "name": "m1", "enabled": True, "can_update": False},
                "p2@m2": {"provider": "p2", "name": "m2", "enabled": True, "can_update": False},
            }
        ),
        encoding="utf-8",
    )
    module_llm_model_registry_boot(
        source_llm_models_store_file=assets_dir / REGISTRY_FILENAME,
        user_llm_models_store_file=data_dir / REGISTRY_FILENAME,
    )
    data = json.loads((data_dir / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data["p1@m1"]["provider"] == "p1" and data["p1@m1"]["name"] == "m1"
    assert data["p2@m2"]["provider"] == "p2" and data["p2@m2"]["name"] == "m2"


def test_module_llm_model_registry_boot_updates_when_source_can_update_false_target_true(
    tmp_path: Path,
) -> None:
    """On boot: source can_update=false and target can_update=true overwrites the record."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    assets_dir.mkdir(parents=True)
    (data_dir / REGISTRY_FILENAME).write_text(
        json.dumps(
            {"p1@m1": {"provider": "p1", "name": "m1", "enabled": True, "can_update": True, "context_window": 100}}
        ),
        encoding="utf-8",
    )
    (assets_dir / REGISTRY_FILENAME).write_text(
        json.dumps(
            {
                "p1@m1": {
                    "provider": "p1",
                    "name": "m1",
                    "enabled": False,
                    "can_update": False,
                    "context_window": 200,
                }
            }
        ),
        encoding="utf-8",
    )
    module_llm_model_registry_boot(
        source_llm_models_store_file=assets_dir / REGISTRY_FILENAME,
        user_llm_models_store_file=data_dir / REGISTRY_FILENAME,
    )
    data = json.loads((data_dir / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data["p1@m1"]["can_update"] is False
    assert data["p1@m1"]["enabled"] is False
    assert data["p1@m1"]["context_window"] == 200


def test_module_llm_model_registry_boot_does_not_overwrite_user_fixed_record(tmp_path: Path) -> None:
    """On boot, records with target.can_update=false are not overwritten from source."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    assets_dir.mkdir(parents=True)
    (data_dir / REGISTRY_FILENAME).write_text(
        json.dumps(
            {
                "p1@m1": {
                    "provider": "p1",
                    "name": "m1",
                    "enabled": True,
                    "can_update": False,
                    "context_window": 111,
                }
            }
        ),
        encoding="utf-8",
    )
    (assets_dir / REGISTRY_FILENAME).write_text(
        json.dumps(
            {
                "p1@m1": {
                    "provider": "p1",
                    "name": "m1",
                    "enabled": False,
                    "can_update": False,
                    "context_window": 999,
                }
            }
        ),
        encoding="utf-8",
    )
    module_llm_model_registry_boot(
        source_llm_models_store_file=assets_dir / REGISTRY_FILENAME,
        user_llm_models_store_file=data_dir / REGISTRY_FILENAME,
    )
    data = json.loads((data_dir / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert data["p1@m1"]["can_update"] is False
    assert data["p1@m1"]["enabled"] is True
    assert data["p1@m1"]["context_window"] == 111


def test_merge_adds_new_record(tmp_path: Path) -> None:
    """Merge: missing provider/name combination is added."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    (data_dir / REGISTRY_FILENAME).write_text("{}", encoding="utf-8")
    assets_dir.mkdir(parents=True)
    (assets_dir / REGISTRY_FILENAME).write_text(
        json.dumps({"p1@m1": {"provider": "p1", "name": "m1", "enabled": True}}),
        encoding="utf-8",
    )
    LLMModelStoreMerger.merge_registry_from_assets(assets_dir, data_dir, REGISTRY_FILENAME)
    data = json.loads((data_dir / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data["p1@m1"]["provider"] == "p1"
    assert data["p1@m1"]["name"] == "m1"


def test_merge_overwrites_when_can_update_true(tmp_path: Path) -> None:
    """Merge: existing record with can_update=true gets fields overwritten."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    (data_dir / REGISTRY_FILENAME).write_text(
        json.dumps({"p1@m1": {"provider": "p1", "name": "m1", "enabled": True, "context_window": 100}}),
        encoding="utf-8",
    )
    assets_dir.mkdir(parents=True)
    (assets_dir / REGISTRY_FILENAME).write_text(
        json.dumps(
            {"p1@m1": {"provider": "p1", "name": "m1", "can_update": True, "enabled": False, "context_window": 200}}
        ),
        encoding="utf-8",
    )
    LLMModelStoreMerger.merge_registry_from_assets(assets_dir, data_dir, REGISTRY_FILENAME)
    data = json.loads((data_dir / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data["p1@m1"]["enabled"] is False and data["p1@m1"]["context_window"] == 200


def test_merge_does_not_overwrite_when_can_update_false(tmp_path: Path) -> None:
    """Merge: existing record with can_update=false is left unchanged."""
    assets_dir = tmp_path / "assets"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True)
    (data_dir / REGISTRY_FILENAME).write_text(
        json.dumps({"p1@m1": {"provider": "p1", "name": "m1", "enabled": True, "context_window": 100}}),
        encoding="utf-8",
    )
    assets_dir.mkdir(parents=True)
    (assets_dir / REGISTRY_FILENAME).write_text(
        json.dumps({"p1@m1": {"provider": "p1", "name": "m1", "can_update": False, "context_window": 999}}),
        encoding="utf-8",
    )
    LLMModelStoreMerger.merge_registry_from_assets(assets_dir, data_dir, REGISTRY_FILENAME)
    data = json.loads((data_dir / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data["p1@m1"]["context_window"] == 100
