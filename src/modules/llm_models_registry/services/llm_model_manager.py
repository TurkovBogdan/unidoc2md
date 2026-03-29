"""Registry manager: add batches of models without duplicates; save once per batch."""

from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path

from ..errors import EmptyModelCodeError, EmptyProviderError
from ..models.llm_model import LLMModel
from ..providers.llm_model_store import LLMModelStore


def _require_provider(provider: str) -> str:
    """Normalize provider (strip); raises EmptyProviderError if empty."""
    p = (provider or "").strip()
    if not p:
        raise EmptyProviderError("provider cannot be empty")
    return p


def _require_name(name: str) -> str:
    """Normalize model name/code (strip); raises EmptyModelCodeError if empty."""
    n = (name or "").strip()
    if not n:
        raise EmptyModelCodeError("model code cannot be empty")
    return n


def _parse_model_key(model_key: str) -> tuple[str, str]:
    """Parse provider@name; raises EmptyProviderError / EmptyModelCodeError on bad format."""
    key = (model_key or "").strip()
    if not key:
        raise EmptyProviderError("model_key cannot be empty")
    if "@" not in key:
        raise EmptyModelCodeError("model_key must be in format provider@name")
    provider, name = key.split("@", 1)
    return (_require_provider(provider), _require_name(name))


def _normalize_model_key(model_key: str) -> str:
    """Normalized provider@name key for store access."""
    provider, name = _parse_model_key(model_key)
    return f"{provider}@{name}"


def _record_key(item: dict) -> str | None:
    """Record key provider@name. None if provider or name is missing."""
    provider = item.get("provider") or item.get("provider_code")
    name = item.get("name") or item.get("code")
    if provider is None or name is None:
        return None
    p = str(provider).strip()
    n = str(name).strip()
    if not p or not n:
        return None
    return f"{p}@{n}"


def _record_sort_key(item: dict) -> tuple[str, int]:
    """Sort key: (provider, -created). Provider ascending, created descending."""
    provider = (item.get("provider") or item.get("provider_code") or "").strip()
    created = item.get("created")
    if created is None:
        created = 0
    try:
        created = int(created)
    except (TypeError, ValueError):
        created = 0
    return (provider, -created)


class LLMModelManager:
    """
    Registry manager: uses storage; default file path from ModuleConfig (models_store_file).
    Adds models only when no row exists for provider@name; saves once after the whole batch.
    """

    def __init__(self, store_file_path: Path | str | None = None) -> None:
        self._store = LLMModelStore(store_file_path=store_file_path)
        self._store.load()

    @staticmethod
    def optional_price_per_million(value: object) -> float | None:
        """
        Price per 1M tokens from registry/UI: unset → None; ``0`` is valid;
        non-numeric, nan, inf → None.
        """
        if value is None:
            return None
        try:
            x = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(x):
            return None
        return x

    @property
    def store(self) -> LLMModelStore:
        """Underlying registry store."""
        return self._store

    def exists(self, model_key: str) -> bool:
        """True if a row exists for the given provider@name key."""
        return _normalize_model_key(model_key) in self._store.data

    def create_empty(
        self,
        model_key: str,
        created: int | None = None,
    ) -> dict:
        """
        Build a model row with defaults: can_update=True, enabled=True.
        Shape matches LLMModel.to_registry_record(); created is a numeric timestamp.
        """
        provider, name = _parse_model_key(model_key)
        model = LLMModel(
            provider=provider,
            name=name,
            can_update=True,
            enabled=True,
        )
        record = model.to_registry_record()
        record["created"] = created
        return record

    def add_models(self, models: Iterable[dict]) -> int:
        """
        Insert rows only when provider@name is not already present.
        Calls store.save() once after the batch.
        Returns the number of rows added. Rows without valid provider/name are skipped.
        """
        existing_keys: set[str] = set(self._store.data.keys())

        added = 0
        for item in models:
            if not isinstance(item, dict):
                continue
            k = _record_key(item)
            if k is None or k in existing_keys:
                continue
            existing_keys.add(k)
            self._store.data[k] = dict(item)
            added += 1

        if added:
            self._store.save()
        return added

    def get_sorted_records(self) -> list[dict]:
        """
        Registry rows sorted by provider name, then by created descending.
        Single entry point for UI lists with this ordering.
        """
        records = [item for item in self._store.data.values() if isinstance(item, dict)]
        return sorted(records, key=_record_sort_key)

    def get_provider_codes(self) -> list[str]:
        """Distinct provider codes from the registry, in sorted-record order."""
        seen: set[str] = set()
        codes: list[str] = []
        for item in self.get_sorted_records():
            p = (item.get("provider") or item.get("provider_code") or "").strip()
            if p and p not in seen:
                seen.add(p)
                codes.append(p)
        return codes

    def get_model_keys(self, only_enabled: bool = True) -> list[str]:
        """Keys as provider@name for UI selection; sort: provider then created desc.
        With only_enabled=True, only rows with enabled=True."""
        sorted_items = sorted(
            self._store.data.items(),
            key=lambda kv: _record_sort_key(kv[1]),
        )
        if not only_enabled:
            return [k for k, _ in sorted_items]
        return [k for k, item in sorted_items if item.get("enabled", True)]

    def get_model_names(self, provider: str) -> list[str]:
        """Model names/codes for a provider, by created descending."""
        p = _require_provider(provider)
        prefix = f"{p}@"
        sorted_items = sorted(
            self._store.data.items(),
            key=lambda kv: _record_sort_key(kv[1]),
        )
        return [key[len(prefix) :] for key, _ in sorted_items if key.startswith(prefix)]

    def get_record(self, model_key: str) -> dict | None:
        """Return the registry row for provider@name or None."""
        key = _normalize_model_key(model_key)
        item = self._store.data.get(key)
        if isinstance(item, dict):
            return item
        return None

    def get_cost(
        self,
        model_key: str,
        input_count: int,
        total_count: int,
    ) -> float | None:
        """
        Cost from registry prices:
        input_count * price_input / 1_000_000 +
        (total_count - input_count) * price_output / 1_000_000.
        Output tokens = total_count - input_count.
        Price ``0`` counts; missing (None / non-numeric) skips that component.
        None if no row or both prices missing.
        """
        record = self.get_record(model_key)
        if record is None:
            return None
        pi = self.optional_price_per_million(record.get("price_input"))
        po = self.optional_price_per_million(record.get("price_output"))
        if pi is None and po is None:
            return None
        output_billable = max(0, total_count - input_count)
        total_cost = 0.0
        if pi is not None:
            total_cost += input_count * pi / 1_000_000
        if po is not None:
            total_cost += output_billable * po / 1_000_000
        return total_cost

    @staticmethod
    def costs_from_price_per_million_tokens(
        price_input_per_million: float | None,
        price_output_per_million: float | None,
        *,
        prompt_tokens: int,
        total_tokens: int,
    ) -> tuple[float | None, float | None]:
        """
        Input and output cost (USD) given prices per 1M tokens.

        Same formula as get_cost: prompt_tokens * price_in / 1e6
        + max(0, total_tokens - prompt_tokens) * price_out / 1e6.
        Everything beyond prompt is billed at output rate (including reasoning in total).
        Price ``0`` yields zero for that component; missing → None for that component.
        """
        cost_in: float | None = None
        cost_out: float | None = None
        try:
            p = max(0, int(prompt_tokens))
            t = max(0, int(total_tokens))
        except (TypeError, ValueError):
            return None, None
        out_toks = max(0, t - p)
        pi = LLMModelManager.optional_price_per_million(price_input_per_million)
        po = LLMModelManager.optional_price_per_million(price_output_per_million)
        if pi is not None:
            cost_in = p * pi / 1_000_000
        if po is not None:
            cost_out = out_toks * po / 1_000_000
        return cost_in, cost_out

    def get_token_billable_costs(
        self,
        model_key: str,
        *,
        prompt_tokens: int,
        total_tokens: int,
    ) -> tuple[float | None, float | None]:
        """
        Input/output cost from registry prices (USD per 1M tokens).
        Output tokens: total_tokens - prompt_tokens (same as get_cost).
        """
        record = self.get_record(model_key)
        if record is None:
            return None, None
        return self.costs_from_price_per_million_tokens(
            record.get("price_input"),
            record.get("price_output"),
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
        )

    def update_model(self, model_key: str, **fields: object) -> bool:
        """
        Update fields on the row for provider@name. Persists registry.
        Returns True if the row existed and was updated.
        """
        key = _normalize_model_key(model_key)
        item = self._store.data.get(key)
        if not isinstance(item, dict):
            return False
        for k, v in fields.items():
            item[k] = v
        self._store.save()
        return True

    def update_user_model(self, model_key: str, **fields: object) -> bool:
        """
        Update as a user edit: sets can_update=False so bootstrap will not overwrite
        from the bundled source.
        """
        fields["can_update"] = False
        return self.update_model(model_key, **fields)
