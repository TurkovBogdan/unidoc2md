"""Load and synchronize ``app.ini`` with the ``AppConfig`` model."""

from __future__ import annotations

import configparser
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, get_type_hints

from src.app_config import AppConfig
from src.core.app_path import resolve_runtime_root

INI_FILENAME = "app.ini"


def _ini_path(root: Path | None = None) -> Path:
    """Path to ``app.ini`` under the runtime root."""
    base = Path(root) if root is not None else resolve_runtime_root()
    return base / INI_FILENAME


def _parse_bool(value: str) -> bool:
    v = (value or "").strip().lower()
    return v in ("true", "1", "yes", "on")


def _ini_section_name(field_name: str, metadata: Any) -> str:
    return str(metadata.get("ini_section", field_name.upper()))


def _ini_key_name(field_name: str, metadata: Any) -> str:
    return str(metadata.get("ini_key", field_name.upper()))


def _serialize_value(value: Any, type_hint: Any) -> str:
    if type_hint is bool:
        return "true" if bool(value) else "false"
    return "" if value is None else str(value)


def _deserialize_value(value: str, type_hint: Any) -> Any:
    if type_hint is bool:
        return _parse_bool(value)
    if type_hint is int:
        try:
            return int((value or "").strip() or 0)
        except ValueError:
            return 0
    return value or ""


def _iter_config_schema() -> list[tuple[str, str, type[Any], list[tuple[str, str, Any]]]]:
    """
    Return the ``AppConfig`` schema:
    ``[(app_field_name, ini_section, section_type, [(field_name, ini_key, field_type), ...]), ...]``
    """
    app_hints = get_type_hints(AppConfig)
    schema: list[tuple[str, str, type[Any], list[tuple[str, str, Any]]]] = []
    for app_field in fields(AppConfig):
        section_type = app_hints.get(app_field.name, app_field.type)
        if not is_dataclass(section_type):
            continue
        section_name = _ini_section_name(app_field.name, app_field.metadata)
        section_hints = get_type_hints(section_type)
        section_fields: list[tuple[str, str, Any]] = []
        for section_field in fields(section_type):
            section_fields.append(
                (
                    section_field.name,
                    _ini_key_name(section_field.name, section_field.metadata),
                    section_hints.get(section_field.name, section_field.type),
                )
            )
        schema.append((app_field.name, section_name, section_type, section_fields))
    return schema


def _config_to_parser(config: AppConfig) -> configparser.RawConfigParser:
    """Build a ``ConfigParser`` from ``AppConfig`` for writing INI (key casing preserved)."""
    p = configparser.RawConfigParser()
    p.optionxform = str  # preserve DEBUG, ANTHROPIC_API_KEY, etc.
    for app_field_name, section_name, _, section_fields in _iter_config_schema():
        section_value = getattr(config, app_field_name)
        p[section_name] = {
            ini_key: _serialize_value(getattr(section_value, field_name), field_type)
            for field_name, ini_key, field_type in section_fields
        }
    return p


def _parser_to_config(parser: configparser.ConfigParser) -> AppConfig:
    """Build ``AppConfig`` from a ``ConfigParser``."""
    def get(section: str, key: str, fallback: str = "") -> str:
        try:
            return parser.get(section, key, fallback=fallback) or ""
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    defaults = AppConfig.default()
    app_kwargs: dict[str, Any] = {}
    for app_field_name, section_name, section_type, section_fields in _iter_config_schema():
        section_defaults = getattr(defaults, app_field_name)
        section_kwargs: dict[str, Any] = {}
        for field_name, ini_key, field_type in section_fields:
            fallback = _serialize_value(getattr(section_defaults, field_name), field_type)
            raw_value = get(section_name, ini_key, fallback)
            section_kwargs[field_name] = _deserialize_value(raw_value, field_type)
        app_kwargs[app_field_name] = section_type(**section_kwargs)
    return AppConfig(**app_kwargs)


def _validate_ini(parser: configparser.ConfigParser) -> bool:
    """Check required sections and keys exist; return True if the file is complete."""
    for _, section_name, _, section_fields in _iter_config_schema():
        if not parser.has_section(section_name):
            return False
        for _, ini_key, _ in section_fields:
            if not parser.has_option(section_name, ini_key):
                return False
    return True


def _create_default_ini(root: Path | None = None) -> None:
    """Create ``app.ini`` from the ``AppConfig.default()`` template."""
    path = _ini_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    config = AppConfig.default()
    parser = _config_to_parser(config)
    with path.open("w", encoding="utf-8") as f:
        parser.write(f)


def _merge_missing_keys(root: Path | None = None) -> None:
    """Add missing sections and keys with defaults to an existing ``app.ini``."""
    path = _ini_path(root)
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    defaults = AppConfig.default()
    changed = False

    for app_field_name, section_name, _, section_fields in _iter_config_schema():
        if not parser.has_section(section_name):
            parser.add_section(section_name)
            changed = True
        section_defaults = getattr(defaults, app_field_name)
        for field_name, ini_key, field_type in section_fields:
            if not parser.has_option(section_name, ini_key):
                default_value = getattr(section_defaults, field_name)
                parser.set(section_name, ini_key, _serialize_value(default_value, field_type))
                changed = True

    if changed:
        with path.open("w", encoding="utf-8") as f:
            parser.write(f)


def _load_config(root: Path | None = None) -> AppConfig:
    """Read ``app.ini`` and return ``AppConfig``. File must exist and be complete after merge."""
    path = _ini_path(root)
    parser = configparser.RawConfigParser()
    parser.optionxform = str
    parser.read(path, encoding="utf-8")
    return _parser_to_config(parser)


def load_or_create(root: Path | None = None) -> AppConfig:
    """
    Ensure ``app.ini`` exists next to the exe or app entrypoint
    (or under an explicit ``root`` for tests/low-level use),
    create from template or merge missing keys, then load config.
    Does not update the runtime store — app code should use ``AppConfigStore.load_or_create()``.
    """
    path = _ini_path(root)
    if not path.exists():
        _create_default_ini(root)
    else:
        _merge_missing_keys(root)
    return _load_config(root)


def save_config(config: AppConfig, root: Path | None = None) -> None:
    """
    Write ``app.ini`` next to the exe or app entrypoint
    (or under an explicit ``root`` for tests/low-level use).
    Does not update the runtime store — app code should use ``AppConfigStore.save(config)``.
    """
    path = _ini_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    parser = _config_to_parser(config)
    with path.open("w", encoding="utf-8") as f:
        parser.write(f)


class AppConfigBuilder:
    """
    Public entry point for working with ``app.ini``.
    Prefer ``AppConfigStore.load_or_create()`` from ``src.core``
    (class-based facade updates the runtime store and resolves the ``app.ini`` path).
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = root

    def build(self) -> AppConfig:
        """Load or create ``app.ini`` and return the current ``AppConfig``."""
        return load_or_create(self._root)
