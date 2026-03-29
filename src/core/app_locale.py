"""Class-based app localization via gettext-style API and JSON catalogs."""

from __future__ import annotations

import gettext
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Callable, Mapping

from .app_config_store import AppConfigStore
from .app_path import project_root, resolve_runtime_root

AVAILABLE_LANGUAGES: dict[str, str] = {}
_LANGUAGE_CHANGE_LISTENERS: list[Callable[[str, str], None]] = []


def first_available_language_code() -> str:
    """First code in the registered list (order as in ``lang_boot`` / ``app.py``)."""
    if not AVAILABLE_LANGUAGES:
        raise ValueError("AVAILABLE_LANGUAGES is empty")
    return next(iter(AVAILABLE_LANGUAGES))


class JsonTranslations(gettext.NullTranslations):
    """gettext-compatible translator backed by a JSON catalog."""

    def __init__(self, catalog: Mapping[str, str] | None = None) -> None:
        super().__init__()
        self._catalog = dict(catalog or {})

    def gettext(self, message: str) -> str:
        return self._catalog.get(message, message)

    def ngettext(self, singular: str, plural: str, n: int) -> str:
        key = singular if n == 1 else plural
        return self._catalog.get(key, key)


def _normalize_language(language: str) -> str:
    code = (language or "").strip().lower().replace("-", "_")
    if not code:
        raise ValueError("language must be non-empty")
    return code


def _resolve_language_file(language: str) -> Path:
    """Catalog file: in dev prefer runtime (after sync), else project tree; frozen uses ``resolve_packaged_locale_path``."""
    code = _normalize_language(language)
    if getattr(sys, "frozen", False):
        return resolve_packaged_locale_path(language)
    rt_file = resolve_runtime_root() / "assets" / "locale" / f"{code}.json"
    if rt_file.is_file():
        return rt_file
    return project_root() / "assets" / "locale" / f"{code}.json"


def _resolve_packaged_locale_root(*, runtime_root: Path | None = None) -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            meipass_locale = Path(meipass) / "assets" / "locale"
            if meipass_locale.is_dir():
                return meipass_locale
        base = runtime_root if runtime_root is not None else resolve_runtime_root()
        return base / "assets" / "locale"
    return project_root() / "assets" / "locale"


def resolve_packaged_locale_path(language: str, *, runtime_root: Path | None = None) -> Path:
    code = _normalize_language(language)
    locale_root = _resolve_packaged_locale_root(runtime_root=runtime_root)
    return locale_root / f"{code}.json"


def _load_catalog(language: str) -> dict[str, str]:
    file_path = _resolve_language_file(language)
    if not file_path.is_file():
        raise FileNotFoundError(f"Locale file not found: {file_path}")
    raw = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Locale file must contain a JSON object: {file_path}")
    catalog: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(f"Locale keys and values must be strings: {file_path}")
        catalog[key] = value
    return catalog


class AppLocaleStore:
    """Single class-based access to gettext-style translators."""

    _current_language: str = ""
    _translations: dict[str, gettext.NullTranslations] = {}

    @classmethod
    def get_language(cls) -> str:
        return cls._current_language

    @classmethod
    def set_language(cls, language: str) -> None:
        code = _normalize_language(language)
        if code not in AVAILABLE_LANGUAGES:
            raise ValueError(f"Unsupported language: {code}")
        cls._current_language = code

    @classmethod
    def get_translation(cls) -> gettext.NullTranslations:
        code = _normalize_language(cls._current_language)
        if code not in AVAILABLE_LANGUAGES:
            raise ValueError(f"Unsupported language: {code}")
        translation = cls._translations.get(code)
        if translation is None:
            translation = JsonTranslations(_load_catalog(code))
            cls._translations[code] = translation
        return translation

    @classmethod
    def gettext(cls, message: str) -> str:
        return cls.get_translation().gettext(message)

    @classmethod
    def reset(cls) -> None:
        cls._current_language = (
            first_available_language_code() if AVAILABLE_LANGUAGES else ""
        )
        cls._translations.clear()


def set_available_languages(languages: Mapping[str, str]) -> None:
    """Configure the set of available application languages."""
    if not languages:
        raise ValueError("languages must be non-empty")
    validated: dict[str, str] = {}
    for code, name in languages.items():
        normalized = _normalize_language(code)
        display_name = (name or "").strip()
        if not display_name:
            raise ValueError(f"Language name must be non-empty: {code}")
        validated[normalized] = display_name
    AVAILABLE_LANGUAGES.clear()
    AVAILABLE_LANGUAGES.update(validated)
    AppLocaleStore._translations.clear()
    if AppLocaleStore._current_language not in AVAILABLE_LANGUAGES:
        AppLocaleStore._current_language = first_available_language_code()


def set_language(language: str) -> None:
    """Set active language, persist it, and notify listeners."""
    previous = AppLocaleStore.get_language()
    AppLocaleStore.set_language(language)
    current_language = AppLocaleStore.get_language()
    current = AppConfigStore.get()
    next_config = replace(current, core=replace(current.core, language=current_language))
    AppConfigStore.save(next_config)
    if current_language != previous:
        for listener in tuple(_LANGUAGE_CHANGE_LISTENERS):
            listener(previous, current_language)


def add_language_change_listener(listener: Callable[[str, str], None]) -> None:
    """Register a language-change callback: ``listener(old_language, new_language)``."""
    if listener not in _LANGUAGE_CHANGE_LISTENERS:
        _LANGUAGE_CHANGE_LISTENERS.append(listener)


def remove_language_change_listener(listener: Callable[[str, str], None]) -> None:
    """Remove a previously registered language-change callback."""
    if listener in _LANGUAGE_CHANGE_LISTENERS:
        _LANGUAGE_CHANGE_LISTENERS.remove(listener)


def language_choice_required() -> bool:
    """True if ``app.ini`` has no valid language code (``[CORE] LANGUAGE``)."""
    code = (AppConfigStore.get().core.language or "").strip().lower().replace("-", "_")
    return not code or code not in AVAILABLE_LANGUAGES


def locmsg(message: str) -> str:
    """Short alias to resolve a localized string."""
    return AppLocaleStore.gettext(message)


__all__ = [
    "AVAILABLE_LANGUAGES",
    "first_available_language_code",
    "set_language",
    "add_language_change_listener",
    "remove_language_change_listener",
    "language_choice_required",
    "locmsg",
]

