"""Tests for LLMModelManager: store, add_models without duplicates, single save."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.modules.llm_models_registry.services.llm_model_manager import LLMModelManager

REGISTRY_FILENAME = "llm_models_registry.json"


def test_manager_store_uses_given_path(tmp_path: Path) -> None:
    """Manager with store_file_path uses that path in the store."""
    store_path = tmp_path / REGISTRY_FILENAME
    manager = LLMModelManager(store_file_path=store_path)
    assert manager.store.store_file_path == store_path


def test_add_models_empty_registry_adds_all(tmp_path: Path) -> None:
    """With an empty registry, add_models adds all records; file reflects them."""
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
    models = [
        {"provider": "a", "name": "m1", "enabled": True},
        {"provider": "b", "name": "m2", "enabled": False},
        {"provider": "c", "name": "m3"},
    ]
    added = manager.add_models(models)
    assert added == 3
    assert len(manager.store.data) == 3
    path = tmp_path / REGISTRY_FILENAME
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data) == 3
    keys = set(data.keys())
    assert keys == {"a@m1", "b@m2", "c@m3"}


def test_add_models_skips_duplicates(tmp_path: Path) -> None:
    """add_models skips duplicate provider@name; only new keys are added."""
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
    manager.store.data = {
        "a@m1": {"provider": "a", "name": "m1", "enabled": True},
    }
    manager.store.save()

    models = [
        {"provider": "a", "name": "m1", "enabled": False},
        {"provider": "x", "name": "m2"},
    ]
    added = manager.add_models(models)
    assert added == 1
    assert len(manager.store.data) == 2
    keys = set(manager.store.data.keys())
    assert keys == {"a@m1", "x@m2"}
    assert manager.store.data["a@m1"]["enabled"] is True


def test_add_models_file_content_matches_store_data(tmp_path: Path) -> None:
    """After add_models, file contents match store.data."""
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
    models = [
        {"provider": "p", "name": "n"},
    ]
    manager.add_models(models)
    path = tmp_path / REGISTRY_FILENAME
    file_data = json.loads(path.read_text(encoding="utf-8"))
    assert file_data == manager.store.data


def test_update_user_model_sets_can_update_false(tmp_path: Path) -> None:
    """User edits always set can_update=False."""
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
    manager.store.data = {
        "p@n": {
            "provider": "p",
            "name": "n",
            "can_update": True,
            "enabled": True,
            "context_window": 100,
        }
    }
    manager.store.save()

    updated = manager.update_user_model("p@n", context_window=250, enabled=False)

    assert updated is True
    assert manager.store.data["p@n"]["context_window"] == 250
    assert manager.store.data["p@n"]["enabled"] is False
    assert manager.store.data["p@n"]["can_update"] is False
    file_data = json.loads((tmp_path / REGISTRY_FILENAME).read_text(encoding="utf-8"))
    assert file_data["p@n"]["can_update"] is False


def test_costs_from_price_per_million_tokens_total_minus_prompt(tmp_path: Path) -> None:
    """Output cost = (total - prompt) * price_output; input = prompt * price_input."""
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
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
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
    # 400 output tokens × 1000 USD/1M = 0.4 USD
    c_in, c_out = manager.costs_from_price_per_million_tokens(
        0.0,
        1000.0,
        prompt_tokens=100,
        total_tokens=500,
    )
    assert c_in == pytest.approx(0.0)
    assert c_out == pytest.approx(0.4)


def test_get_cost_partial_prices(tmp_path: Path) -> None:
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
    manager.store.data = {
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
    manager.store.save()
    assert manager.get_cost("p@only_in", 1_000_000, 2_000_000) == pytest.approx(2.0)
    assert manager.get_cost("p@only_out", 1_000_000, 2_000_000) == pytest.approx(3.0)


def test_get_token_billable_costs_uses_registry_record(tmp_path: Path) -> None:
    manager = LLMModelManager(store_file_path=tmp_path / REGISTRY_FILENAME)
    manager.store.data = {
        "x@m": {
            "provider": "x",
            "name": "m",
            "price_input": 10.0,
            "price_output": 20.0,
        }
    }
    manager.store.save()
    a, b = manager.get_token_billable_costs(
        "x@m",
        prompt_tokens=1_000_000,
        total_tokens=1_500_000,
    )
    assert a == pytest.approx(10.0)
    assert b == pytest.approx(10.0)
