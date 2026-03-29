"""Tests for LLMModelManager: add_models without duplicates, single save, get_models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.modules.llm_models_registry.services.llm_model_manager import LLMModelManager
from tests.modules.llm_models_registry.support import bind_registry

REGISTRY_FILENAME = "llm_models_registry.json"


def _keyed_models(manager: LLMModelManager) -> dict[str, dict]:
    return {
        f"{r.get('provider')}@{r.get('name')}": dict(r)
        for r in manager.get_models()
        if r.get("provider") is not None and r.get("name") is not None
    }


def test_manager_store_file_path_uses_config_path(tmp_path: Path) -> None:
    store_path = tmp_path / REGISTRY_FILENAME
    bind_registry(store_path)
    manager = LLMModelManager()
    assert manager.store_file_path == store_path.resolve()


def test_add_models_empty_registry_adds_all(tmp_path: Path) -> None:
    bind_registry(tmp_path / REGISTRY_FILENAME)
    manager = LLMModelManager()
    models = [
        {"provider": "a", "name": "m1", "enabled": True},
        {"provider": "b", "name": "m2", "enabled": False},
        {"provider": "c", "name": "m3"},
    ]
    added = manager.add_models(models)
    assert added == 3
    assert len(manager.get_models()) == 3
    path = tmp_path / REGISTRY_FILENAME
    assert path.exists()
    file_data = json.loads(path.read_text(encoding="utf-8"))
    assert len(file_data) == 3
    assert set(file_data.keys()) == {"a@m1", "b@m2", "c@m3"}


def test_add_models_skips_duplicates(tmp_path: Path) -> None:
    path = tmp_path / REGISTRY_FILENAME
    path.write_text(
        json.dumps({"a@m1": {"provider": "a", "name": "m1", "enabled": True}}),
        encoding="utf-8",
    )
    bind_registry(path)
    manager = LLMModelManager()

    models = [
        {"provider": "a", "name": "m1", "enabled": False},
        {"provider": "x", "name": "m2"},
    ]
    added = manager.add_models(models)
    assert added == 1
    assert len(manager.get_models()) == 2
    keys = set(_keyed_models(manager).keys())
    assert keys == {"a@m1", "x@m2"}
    assert _keyed_models(manager)["a@m1"]["enabled"] is True


def test_add_models_file_content_matches_get_models(tmp_path: Path) -> None:
    bind_registry(tmp_path / REGISTRY_FILENAME)
    manager = LLMModelManager()
    models = [
        {"provider": "p", "name": "n"},
    ]
    manager.add_models(models)
    path = tmp_path / REGISTRY_FILENAME
    file_data = json.loads(path.read_text(encoding="utf-8"))
    assert file_data == _keyed_models(manager)


def test_update_user_model_sets_can_update_false(tmp_path: Path) -> None:
    path = tmp_path / REGISTRY_FILENAME
    path.write_text(
        json.dumps(
            {
                "p@n": {
                    "provider": "p",
                    "name": "n",
                    "can_update": True,
                    "enabled": True,
                    "context_window": 100,
                }
            }
        ),
        encoding="utf-8",
    )
    bind_registry(path)
    manager = LLMModelManager()

    updated = manager.update_user_model("p@n", context_window=250, enabled=False)

    assert updated is True
    row = manager.get_model("p@n")
    assert row is not None
    assert row["context_window"] == 250
    assert row["enabled"] is False
    assert row["can_update"] is False
    file_data = json.loads(path.read_text(encoding="utf-8"))
    assert file_data["p@n"]["can_update"] is False


def test_costs_from_price_per_million_tokens_total_minus_prompt(tmp_path: Path) -> None:
    bind_registry(tmp_path / REGISTRY_FILENAME)
    manager = LLMModelManager()
    c_in, c_out = manager.costs_from_price_per_million_tokens(
        1_000_000.0,
        2_000_000.0,
        prompt_tokens=2,
        total_tokens=10,
    )
    assert c_in == pytest.approx(2.0)
    assert c_out == pytest.approx(16.0)


def test_optional_price_per_million_none_zero_and_invalid() -> None:
    assert LLMModelManager.optional_price_per_million(None) is None
    assert LLMModelManager.optional_price_per_million(0) == 0.0
    assert LLMModelManager.optional_price_per_million(0.0) == 0.0
    assert LLMModelManager.optional_price_per_million(float("nan")) is None
    assert LLMModelManager.optional_price_per_million("x") is None


def test_costs_from_price_zero_input_price_still_bills_output(tmp_path: Path) -> None:
    bind_registry(tmp_path / REGISTRY_FILENAME)
    manager = LLMModelManager()
    c_in, c_out = manager.costs_from_price_per_million_tokens(
        0.0,
        1000.0,
        prompt_tokens=100,
        total_tokens=500,
    )
    assert c_in == pytest.approx(0.0)
    assert c_out == pytest.approx(0.4)


def test_get_cost_partial_prices(tmp_path: Path) -> None:
    path = tmp_path / REGISTRY_FILENAME
    path.write_text(
        json.dumps(
            {
                "p@only_in": {
                    "provider": "p",
                    "name": "only_in",
                    "price_input": 2.0,
                },
                "p@only_out": {
                    "provider": "p",
                    "name": "only_out",
                    "price_output": 3.0,
                },
            }
        ),
        encoding="utf-8",
    )
    bind_registry(path)
    manager = LLMModelManager()
    assert manager.get_cost("p@only_in", 1_000_000, 2_000_000) == pytest.approx(2.0)
    assert manager.get_cost("p@only_out", 1_000_000, 2_000_000) == pytest.approx(3.0)


def test_get_token_billable_costs_uses_registry_record(tmp_path: Path) -> None:
    path = tmp_path / REGISTRY_FILENAME
    path.write_text(
        json.dumps(
            {
                "x@m": {
                    "provider": "x",
                    "name": "m",
                    "price_input": 10.0,
                    "price_output": 20.0,
                }
            }
        ),
        encoding="utf-8",
    )
    bind_registry(path)
    manager = LLMModelManager()
    a, b = manager.get_token_billable_costs(
        "x@m",
        prompt_tokens=1_000_000,
        total_tokens=1_500_000,
    )
    assert a == pytest.approx(10.0)
    assert b == pytest.approx(10.0)
