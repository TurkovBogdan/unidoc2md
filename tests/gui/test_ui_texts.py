"""Tests for the UI text registry: screen titles and key strings."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core import AppConfigStore
from src.core.app_locale import AppLocaleStore, set_available_languages
from tests.gui.ui_texts_fixtures import (
    EXPECTED_BUTTON_LABELS,
    EXPECTED_PAGE_TITLES,
    EXPECTED_SCREEN_TITLES,
)


@pytest.fixture(autouse=True)
def _configure_languages(tmp_path: Path) -> None:
    AppConfigStore.reset()
    AppConfigStore.load_or_create(tmp_path)
    set_available_languages(
        {
            "ru": "Русский",
            "en": "English",
            "zh": "中文",
        }
    )
    AppLocaleStore.reset()


def test_screen_titles_exist_in_expected_set() -> None:
    """Localized window titles (ru) stay in the UI text registry."""
    from src.core import locmsg, set_language

    set_language("ru")
    collected = {
        locmsg("gui.window_title"),
        locmsg("home.window_title"),
        f"unidoc2md | {locmsg('settings.title')}",
        locmsg("models.window_title"),
        locmsg("models.detail.window_title"),
        locmsg("project_execution.window_title"),
        locmsg("app.title"),
    }
    for title in collected:
        assert title in EXPECTED_SCREEN_TITLES, f"{title!r} missing from ui_texts_fixtures registry"
    tpl = locmsg("project.window_title")
    assert "unidoc2md" in tpl and "{name}" in tpl


def test_expected_button_labels_non_empty() -> None:
    """Button registry is non-empty and includes core actions."""
    assert len(EXPECTED_BUTTON_LABELS) >= 8
    assert "Сохранить" in EXPECTED_BUTTON_LABELS
    assert "Отмена" in EXPECTED_BUTTON_LABELS


def test_expected_page_titles_non_empty() -> None:
    """Page title registry is non-empty."""
    assert len(EXPECTED_PAGE_TITLES) >= 3
    assert "Проекты" in EXPECTED_PAGE_TITLES
