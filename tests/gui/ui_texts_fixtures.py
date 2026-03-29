"""UI text registry fixtures for tests. Keep in sync with src/gui/docs/ui-texts.md when present."""

from __future__ import annotations

# Expected window titles (ru locale strings from locale/ru/*.json)
EXPECTED_SCREEN_TITLES = {
    "unidoc2md — Конфигуратор проектов",
    "unidoc2md | Проекты",
    "unidoc2md | Настройки",
    "unidoc2md | Настройка моделей",
    "unidoc2md | Редактирование модели",
    "unidoc2md | Выполнение",
    "unidoc2md",
}

# Key button / action labels (documentation registry check)
EXPECTED_BUTTON_LABELS = frozenset({
    "Вернуться",
    "Назад",
    "Сохранить",
    "Запустить",
    "Отмена",
    "ОК",
    "Создать",
    "Удалить",
    "Открыть",
    "Открыть папку",
    "Настройки",
    "Настройка моделей",
    "Редактировать",
    "Синхронизировать",
})

# Page-level headings (first level)
EXPECTED_PAGE_TITLES = frozenset({
    "Проекты",
    "Настройки",
    "Модели",
})
