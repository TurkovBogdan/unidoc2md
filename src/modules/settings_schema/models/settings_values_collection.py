"""Collection of settings group values."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.modules.settings_schema.exceptions import SettingsSchemaError
from src.modules.settings_schema.models.settings_group_values import SettingsGroupValues


@dataclass(frozen=True)
class SettingsValuesCollection:
    """Single collection of per-group settings values."""

    groups: tuple[SettingsGroupValues, ...] = ()

    def __post_init__(self) -> None:
        codes = [group.code for group in self.groups]
        duplicated = {code for code in codes if codes.count(code) > 1}
        if duplicated:
            names = ", ".join(sorted(duplicated))
            raise SettingsSchemaError(f"Values collection contains duplicated group codes: {names}")

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> "SettingsValuesCollection":
        """Build from a top-level payload mapping (group_code -> field dict)."""
        if payload is None:
            return cls()
        if not isinstance(payload, Mapping):
            raise SettingsSchemaError("Values collection payload must be an object")
        groups = tuple(
            SettingsGroupValues.from_payload(str(code), group_payload)
            for code, group_payload in payload.items()
        )
        return cls(groups=groups)

    @classmethod
    def from_json(cls, raw_json: str) -> "SettingsValuesCollection":
        """Build from a JSON string."""
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise SettingsSchemaError(f"Invalid values collection JSON: {e}") from e
        return cls.from_payload(payload)

    def get_group(self, code: str) -> SettingsGroupValues | None:
        """Return values group by code, or None."""
        for group in self.groups:
            if group.code == code:
                return group
        return None

    def get_group_value(self, code: str, key: str, default: Any = None) -> Any:
        """Return a field value for a group by group code and field key."""
        group = self.get_group(code)
        if group is None:
            return default
        return group.get_value(key, default)

    def to_payload(self) -> dict[str, dict[str, Any]]:
        """Return payload for all groups."""
        return {group.code: group.to_payload() for group in self.groups}
