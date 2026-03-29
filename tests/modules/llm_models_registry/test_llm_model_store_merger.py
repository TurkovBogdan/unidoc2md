"""Unit tests for LLMModelStoreMerger: missing files, bad JSON, and merge edge cases."""

from __future__ import annotations

import json
from pathlib import Path

from src.modules.llm_models_registry.boot import LLMModelStoreMerger

REGISTRY_FILENAME = "llm_models_registry.json"


def test_apply_boot_merge_creates_empty_target_when_both_source_and_target_missing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "missing_source.json"
    target = tmp_path / "out" / REGISTRY_FILENAME
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == {}


def test_apply_boot_merge_new_target_malformed_source_writes_empty_dict(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text("{ not json", encoding="utf-8")
    target = tmp_path / "user" / REGISTRY_FILENAME
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == {}


def test_apply_boot_merge_existing_target_unchanged_when_source_missing(tmp_path: Path) -> None:
    source = tmp_path / "no_such_source.json"
    target = tmp_path / REGISTRY_FILENAME
    payload = {"a@b": {"provider": "a", "name": "b", "enabled": True}}
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.read_text(encoding="utf-8") == before


def test_apply_boot_merge_existing_target_unchanged_when_source_invalid_json(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.json"
    source.write_text("{broken", encoding="utf-8")
    target = tmp_path / REGISTRY_FILENAME
    payload = {"x@y": {"provider": "x", "name": "y"}}
    target.write_text(json.dumps(payload), encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.read_text(encoding="utf-8") == before


def test_apply_boot_merge_existing_target_unchanged_when_source_empty_map(
    tmp_path: Path,
) -> None:
    source = tmp_path / "empty.json"
    source.write_text("{}", encoding="utf-8")
    target = tmp_path / REGISTRY_FILENAME
    payload = {"p@m": {"provider": "p", "name": "m", "can_update": False}}
    target.write_text(json.dumps(payload), encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.read_text(encoding="utf-8") == before


def test_apply_boot_merge_existing_target_unchanged_when_source_only_non_dict_values(
    tmp_path: Path,
) -> None:
    source = tmp_path / "weird.json"
    source.write_text(json.dumps({"a": 1, "b": "skip", "c": []}), encoding="utf-8")
    target = tmp_path / REGISTRY_FILENAME
    payload = {"p@m": {"provider": "p", "name": "m"}}
    target.write_text(json.dumps(payload), encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.read_text(encoding="utf-8") == before


def test_apply_boot_merge_existing_target_unchanged_when_target_json_corrupt(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps({"n@m": {"provider": "n", "name": "m"}}),
        encoding="utf-8",
    )
    target = tmp_path / REGISTRY_FILENAME
    target.write_text("{ corrupt", encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.read_text(encoding="utf-8") == before


def test_apply_boot_merge_source_json_array_new_target_writes_empty(tmp_path: Path) -> None:
    source = tmp_path / "list.json"
    source.write_text("[]", encoding="utf-8")
    target = tmp_path / "new" / REGISTRY_FILENAME
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert json.loads(target.read_text(encoding="utf-8")) == {}


def test_apply_boot_merge_source_json_array_existing_target_no_op(tmp_path: Path) -> None:
    source = tmp_path / "list.json"
    source.write_text("[]", encoding="utf-8")
    target = tmp_path / REGISTRY_FILENAME
    payload = {"a@b": {"provider": "a", "name": "b"}}
    target.write_text(json.dumps(payload), encoding="utf-8")
    before = target.read_text(encoding="utf-8")
    LLMModelStoreMerger.apply_boot_merge(source, target)
    assert target.read_text(encoding="utf-8") == before


def test_merge_registry_from_assets_no_source_file_does_not_create_target(
    tmp_path: Path,
) -> None:
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    assets.mkdir()
    LLMModelStoreMerger.merge_registry_from_assets(assets, data, REGISTRY_FILENAME)
    assert data.is_dir()
    assert not (data / REGISTRY_FILENAME).exists()


def test_merge_registry_from_assets_creates_target_from_source_when_target_missing(
    tmp_path: Path,
) -> None:
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    assets.mkdir()
    (assets / REGISTRY_FILENAME).write_text(
        json.dumps({"u@v": {"provider": "u", "name": "v", "enabled": True}}),
        encoding="utf-8",
    )
    LLMModelStoreMerger.merge_registry_from_assets(assets, data, REGISTRY_FILENAME)
    path = data / REGISTRY_FILENAME
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["u@v"]["provider"] == "u"


def test_merge_registry_from_assets_invalid_source_json_does_not_create_target(
    tmp_path: Path,
) -> None:
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    assets.mkdir()
    (assets / REGISTRY_FILENAME).write_text("{bad", encoding="utf-8")
    LLMModelStoreMerger.merge_registry_from_assets(assets, data, REGISTRY_FILENAME)
    assert not (data / REGISTRY_FILENAME).exists()


def test_merge_registry_from_assets_invalid_source_does_not_touch_existing_target(
    tmp_path: Path,
) -> None:
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    data.mkdir()
    assets.mkdir()
    (data / REGISTRY_FILENAME).write_text(
        json.dumps({"keep@me": {"provider": "keep", "name": "me"}}),
        encoding="utf-8",
    )
    (assets / REGISTRY_FILENAME).write_text("not-json", encoding="utf-8")
    before = (data / REGISTRY_FILENAME).read_text(encoding="utf-8")
    LLMModelStoreMerger.merge_registry_from_assets(assets, data, REGISTRY_FILENAME)
    assert (data / REGISTRY_FILENAME).read_text(encoding="utf-8") == before


def test_merge_registry_from_assets_corrupt_target_rebuilt_from_valid_source(
    tmp_path: Path,
) -> None:
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    data.mkdir()
    assets.mkdir()
    (data / REGISTRY_FILENAME).write_text("{broken", encoding="utf-8")
    (assets / REGISTRY_FILENAME).write_text(
        json.dumps({"fix@it": {"provider": "fix", "name": "it"}}),
        encoding="utf-8",
    )
    LLMModelStoreMerger.merge_registry_from_assets(assets, data, REGISTRY_FILENAME)
    loaded = json.loads((data / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert "fix@it" in loaded
    assert loaded["fix@it"]["name"] == "it"


def test_merge_registry_from_assets_empty_normalized_source_no_write_when_target_exists(
    tmp_path: Path,
) -> None:
    assets = tmp_path / "assets"
    data = tmp_path / "data"
    data.mkdir()
    assets.mkdir()
    (data / REGISTRY_FILENAME).write_text(
        json.dumps({"only@one": {"provider": "only", "name": "one"}}),
        encoding="utf-8",
    )
    (assets / REGISTRY_FILENAME).write_text(
        json.dumps({"x": 1, "y": "z"}),
        encoding="utf-8",
    )
    before = (data / REGISTRY_FILENAME).read_text(encoding="utf-8")
    LLMModelStoreMerger.merge_registry_from_assets(assets, data, REGISTRY_FILENAME)
    assert (data / REGISTRY_FILENAME).read_text(encoding="utf-8") == before


def test_to_record_map_uses_outer_key_when_record_missing_provider_name() -> None:
    raw = {"custom-key": {"foo": 1}}
    m = LLMModelStoreMerger._to_record_map(raw)
    assert m == {"custom-key": {"foo": 1}}


def test_can_update_from_record_defaults_false() -> None:
    assert LLMModelStoreMerger._can_update_from_record({}) is False
    assert LLMModelStoreMerger._can_update_from_record({"can_update": True}) is True
