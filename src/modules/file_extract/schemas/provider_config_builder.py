"""Extract settings schema and runtime config assembly. Thin wrapper over SettingsSchemaCollection. Payload shape: group_code -> values."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..models import ExtractConfig
from ..providers.file_extract_provider import get_provider_settings_groups
from src.modules.settings_schema.models import SettingsSchemaCollection


def _build_extract_schema_collection() -> SettingsSchemaCollection:
    """Single collection of groups: extract providers (PDF, images, text, markdown, office)."""
    provider_groups = get_provider_settings_groups()
    return SettingsSchemaCollection(groups=provider_groups)


# Lazy build to avoid circular imports on first access
_EXTRACT_SCHEMA: SettingsSchemaCollection | None = None


def get_extract_settings_schema() -> SettingsSchemaCollection:
    """Canonical extract settings schema for GUI and normalization."""
    global _EXTRACT_SCHEMA
    if _EXTRACT_SCHEMA is None:
        _EXTRACT_SCHEMA = _build_extract_schema_collection()
    return _EXTRACT_SCHEMA


def get_default_extract_payload() -> dict[str, dict[str, Any]]:
    """Default extract payload. Shape: group_code -> values."""
    return get_extract_settings_schema().build_default_payload()


def normalize_extract_payload(raw: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """
    Normalize a raw extract payload against the schema. Shape: group_code -> values.
    If raw is missing or empty, returns the default payload.
    """
    if not raw or not isinstance(raw, dict):
        return get_default_extract_payload()
    return get_extract_settings_schema().normalize_payload(raw)


def build_extract_config(
    project_path: Path | str,
    extract_payload: dict[str, Any] | None,
    cache_path: Path | None = None,
) -> ExtractConfig:
    """
    Build ExtractConfig from an extract payload.
    Payload shape: group_code -> values (providers at the top level).
    Normalization fills defaults from the schema.
    """
    normalized = normalize_extract_payload(extract_payload)
    schema = get_extract_settings_schema()
    provider_configs: dict[str, dict[str, Any]] = {}
    for group in schema.groups:
        provider_configs[group.code] = dict(normalized.get(group.code) or {})

    return ExtractConfig(
        project_path=project_path,
        provider_configs=provider_configs,
        cache_path=cache_path,
    )
