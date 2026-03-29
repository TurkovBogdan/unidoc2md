"""Schema for a single settings field."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.modules.settings_schema.constants import SettingFieldType
from src.modules.settings_schema.exceptions import SettingsSchemaError


@dataclass(frozen=True)
class SettingFieldSchema:
    """Declarative definition of one field in a settings schema.
    For ``type='select'``, ``options`` are ``(code, display_label)`` pairs.
    """

    key: str
    type: SettingFieldType
    default: Any
    label: str
    description: str = ""
    options: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise SettingsSchemaError("Field key must be non-empty")
        if not self.label.strip():
            raise SettingsSchemaError("Field label must be non-empty")
        if self.type == "select":
            if not self.options:
                raise SettingsSchemaError("Select field must define non-empty options")
            for item in self.options:
                if not isinstance(item, (list, tuple)) or len(item) != 2:
                    raise SettingsSchemaError(
                        "Select options must be tuples (code, display)"
                    )
                code, display = item
                if not isinstance(code, str) or not code.strip():
                    raise SettingsSchemaError("Select option code must be non-empty string")
                if not isinstance(display, str) or not display.strip():
                    raise SettingsSchemaError("Select option display must be non-empty string")

    @property
    def option_codes(self) -> tuple[str, ...]:
        """Option codes for ``select`` fields (validation and normalization)."""
        return tuple(c for c, _ in self.options)
