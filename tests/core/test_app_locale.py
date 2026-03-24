"""Тесты core-локализации через AppLocaleStore."""

from __future__ import annotations

import gettext
import sys
from pathlib import Path

import pytest

from src.core.app_locale import (
    AVAILABLE_LANGUAGES,
    AppLocaleStore,
    first_available_language_code,
    locmsg,
    resolve_packaged_locale_path,
    set_available_languages,
    set_language,
)
from src.core.app_path import project_root


@pytest.fixture(autouse=True)
def _configure_languages() -> None:
    set_available_languages(
        {
            "ru": "Русский",
            "en": "English",
            "zh": "中文",
        }
    )
    AppLocaleStore.reset()


def test_get_translation_returns_gettext_instance() -> None:
    translation = AppLocaleStore.get_translation()
    assert isinstance(translation, gettext.NullTranslations)


def test_gettext_uses_ru_catalog_and_fallback_to_key() -> None:
    set_language("ru")
    assert AppLocaleStore.gettext("error.project_not_found") == "Проект не найден"
    assert AppLocaleStore.gettext("unknown.translation.key") == "unknown.translation.key"


def test_locmsg_alias_uses_store_gettext() -> None:
    set_language("ru")
    assert locmsg("error.project_not_found") == "Проект не найден"
    assert locmsg("unknown.translation.key") == "unknown.translation.key"


def test_set_language_rejects_unsupported_code() -> None:
    with pytest.raises(ValueError):
        set_language("de")


def test_reset_restores_first_available_language() -> None:
    AppLocaleStore.reset()
    assert AppLocaleStore.get_language() == "ru"
    assert first_available_language_code() == "ru"


def test_available_languages_has_display_name_map() -> None:
    assert AVAILABLE_LANGUAGES == {
        "ru": "Русский",
        "en": "English",
        "zh": "中文",
    }


def test_set_language_en_and_locmsg() -> None:
    set_language("en")
    assert locmsg("error.project_not_found") == "Project not found"


def test_set_language_zh_and_locmsg() -> None:
    set_language("zh")
    assert locmsg("error.project_not_found") == "未找到项目"


def test_resolve_packaged_locale_path_source_tree() -> None:
    p = resolve_packaged_locale_path("ru")
    assert p == project_root() / "assets" / "locale" / "ru.json"
    assert p.is_file()


def test_resolve_packaged_locale_path_frozen_prefers_meipass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    me = tmp_path / "meipass"
    (me / "assets" / "locale").mkdir(parents=True)
    bundled = me / "assets" / "locale" / "ru.json"
    bundled.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(me), raising=False)
    p = resolve_packaged_locale_path("ru", runtime_root=tmp_path / "exe_dir")
    assert p == bundled

