"""Values for one settings group."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from src.modules.settings_schema.exceptions import SettingsSchemaError


@dataclass(frozen=True)
class SettingsGroupValues:
    """Normalized values for a single settings group."""

    code: str
    values: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise SettingsSchemaError("Values group code must be non-empty")

    @classmethod
    def from_payload(cls, code: str, payload: Mapping[str, Any] | None) -> "SettingsGroupValues":
        """Build from a payload mapping."""
        if payload is None:
            return cls(code=code, values={})
        if not isinstance(payload, Mapping):
            raise SettingsSchemaError("Values group payload must be an object")
        return cls(code=code, values=dict(payload))

    @classmethod
    def from_json(cls, code: str, raw_json: str) -> "SettingsGroupValues":
        """Build from a JSON string."""
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise SettingsSchemaError(f"Invalid values group JSON: {e}") from e
        return cls.from_payload(code, payload)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Return a field value by key."""
        return self.values.get(key, default)

    def to_payload(self) -> dict[str, Any]:
        """Return a copy of the group payload."""
        return dict(self.values)
