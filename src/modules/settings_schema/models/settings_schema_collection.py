"""Collection of settings schema groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.modules.settings_schema.exceptions import SettingsSchemaError
from src.modules.settings_schema.models.settings_group_schema import SettingsGroupSchema
from src.modules.settings_schema.models.settings_values_collection import SettingsValuesCollection


@dataclass(frozen=True)
class SettingsSchemaCollection:
    """Single collection of settings schema groups."""

    groups: tuple[SettingsGroupSchema, ...] = ()

    def __post_init__(self) -> None:
        codes = [group.code for group in self.groups]
        duplicated = {code for code in codes if codes.count(code) > 1}
        if duplicated:
            names = ", ".join(sorted(duplicated))
            raise SettingsSchemaError(f"Collection contains duplicated group codes: {names}")

    def get_group(self, code: str) -> SettingsGroupSchema | None:
        """Return schema group by code, or None."""
        for group in self.groups:
            if group.code == code:
                return group
        return None

    def build_default_payload(self) -> dict[str, dict[str, Any]]:
        """Build default payload for every group in the collection."""
        return {group.code: group.build_default_values() for group in self.groups}

    def validate_values(self, raw_values: SettingsValuesCollection | Mapping[str, Any] | None) -> None:
        """Validate all group values against this schema collection."""
        source = self._coerce_values_source(raw_values)
        unknown_codes = set(source) - {group.code for group in self.groups}
        if unknown_codes:
            names = ", ".join(sorted(unknown_codes))
            raise SettingsSchemaError(f"Values collection contains unknown group codes: {names}")

        for group in self.groups:
            group.validate_values(source.get(group.code))

    def apply_values(self, raw_values: SettingsValuesCollection | Mapping[str, Any] | None) -> SettingsValuesCollection:
        """Apply schemas to all groups and return a normalized ``SettingsValuesCollection``."""
        self.validate_values(raw_values)
        source = self._coerce_values_source(raw_values)
        return SettingsValuesCollection(
            groups=tuple(
                group.apply_values(source.get(group.code))
                for group in self.groups
            )
        )

    def normalize_payload(self, raw_payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
        """Normalize a raw payload for every group."""
        source = raw_payload if isinstance(raw_payload, Mapping) else {}
        return {
            group.code: group.normalize_values(source.get(group.code))
            for group in self.groups
        }

    def _coerce_values_source(
        self,
        raw_values: SettingsValuesCollection | Mapping[str, Any] | None,
    ) -> Mapping[str, Any]:
        if raw_values is None:
            return {}
        if isinstance(raw_values, SettingsValuesCollection):
            return {
                group.code: group.values
                for group in raw_values.groups
            }
        if isinstance(raw_values, Mapping):
            return raw_values
        raise SettingsSchemaError("Values collection must be a values object or mapping")
