"""Schema for one settings group."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from src.modules.settings_schema.exceptions import SettingsSchemaError
from src.modules.settings_schema.models.setting_field_schema import SettingFieldSchema
from src.modules.settings_schema.models.settings_group_values import SettingsGroupValues


_TRUE_VALUES = {"true", "1", "yes", "on"}
_FALSE_VALUES = {"false", "0", "no", "off"}


@dataclass(frozen=True)
class SettingsGroupSchema:
    """Settings schema group with a code and display metadata."""

    code: str
    title: str
    description: str = ""
    fields: tuple[SettingFieldSchema, ...] = ()

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise SettingsSchemaError("Group code must be non-empty")
        if not self.title.strip():
            raise SettingsSchemaError("Group title must be non-empty")

        keys = [field.key for field in self.fields]
        duplicated = {key for key in keys if keys.count(key) > 1}
        if duplicated:
            names = ", ".join(sorted(duplicated))
            raise SettingsSchemaError(f"Group contains duplicated field keys: {names}")

    def get_field(self, key: str) -> SettingFieldSchema | None:
        """Return field schema by key, or None."""
        for field in self.fields:
            if field.key == key:
                return field
        return None

    def build_default_values(self) -> dict[str, Any]:
        """Build default-value dict for the group."""
        return {field.key: field.default for field in self.fields}

    def validate_values(self, raw_values: SettingsGroupValues | Mapping[str, Any] | None) -> None:
        """Validate group values against this schema."""
        source = self._coerce_values_source(raw_values)
        unknown_keys = set(source) - {field.key for field in self.fields}
        if unknown_keys:
            names = ", ".join(sorted(unknown_keys))
            raise SettingsSchemaError(f"Group {self.code!r} contains unknown keys: {names}")

        for field in self.fields:
            if field.key not in source or source[field.key] is None:
                continue
            self._validate_field_value(field, source[field.key])

    def apply_values(self, raw_values: SettingsGroupValues | Mapping[str, Any] | None) -> SettingsGroupValues:
        """Validate and normalize group values into a ``SettingsGroupValues`` instance."""
        self.validate_values(raw_values)
        source = self._coerce_values_source(raw_values)
        return SettingsGroupValues(
            code=self.code,
            values=self.normalize_values(source),
        )

    def normalize_values(self, raw_values: Mapping[str, Any] | None) -> dict[str, Any]:
        """Normalize values by field types and schema defaults."""
        source = raw_values if isinstance(raw_values, Mapping) else {}
        out: dict[str, Any] = {}
        for field in self.fields:
            value = source.get(field.key)
            if value is None:
                out[field.key] = field.default
            elif field.type == "select":
                out[field.key] = value if value in field.option_codes else field.default
            elif field.type == "bool":
                out[field.key] = self._normalize_bool_value(value, field.default)
            elif field.type == "int":
                try:
                    number = int(value)
                    out[field.key] = number if number >= 0 else field.default
                except (TypeError, ValueError):
                    out[field.key] = field.default
            else:
                out[field.key] = value
        return out

    def _coerce_values_source(self, raw_values: SettingsGroupValues | Mapping[str, Any] | None) -> Mapping[str, Any]:
        if raw_values is None:
            return {}
        if isinstance(raw_values, SettingsGroupValues):
            if raw_values.code != self.code:
                raise SettingsSchemaError(
                    f"Values group code mismatch: expected {self.code!r}, got {raw_values.code!r}"
                )
            return raw_values.values
        if isinstance(raw_values, Mapping):
            return raw_values
        raise SettingsSchemaError("Group values must be a values object or mapping")

    def _validate_field_value(self, field: SettingFieldSchema, value: Any) -> None:
        if field.type == "select" and value not in field.option_codes:
            codes = ", ".join(field.option_codes)
            raise SettingsSchemaError(
                f"Field {field.key!r} in group {self.code!r} must be one of: {codes}"
            )
        if field.type == "bool":
            self._normalize_bool_value(value, field.default)
            return
        if field.type == "int":
            try:
                number = int(value)
            except (TypeError, ValueError) as e:
                raise SettingsSchemaError(
                    f"Field {field.key!r} in group {self.code!r} must be an integer"
                ) from e
            if number < 0:
                raise SettingsSchemaError(
                    f"Field {field.key!r} in group {self.code!r} must be >= 0"
                )

    def _normalize_bool_value(self, value: Any, default: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            if value in (0, 1):
                return bool(value)
            raise SettingsSchemaError("Boolean field accepts only 0 or 1 as integer values")
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in _TRUE_VALUES:
                return True
            if normalized in _FALSE_VALUES:
                return False
            raise SettingsSchemaError("Boolean field contains unsupported string value")
        if value is None:
            return bool(default)
        raise SettingsSchemaError("Boolean field contains unsupported value type")
