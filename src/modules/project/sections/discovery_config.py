"""Обработчик секции discovery конфигурации проекта: умолчания и валидация."""

from __future__ import annotations

from typing import Any


class DiscoveryConfig:
    """Статический класс для работы с секцией discovery (config.json)."""

    KEY_RECURSIVE_SEARCH = "recursive_search"

    @staticmethod
    def get_default() -> dict[str, Any]:
        """Возвращает словарь умолчаний для секции discovery."""
        return {DiscoveryConfig.KEY_RECURSIVE_SEARCH: True}

    @staticmethod
    def validate(data: Any) -> list[str]:
        """Проверяет данные секции discovery. Возвращает список сообщений об ошибках (пустой — данные валидны)."""
        errors: list[str] = []
        if not isinstance(data, dict):
            errors.append("Discovery: ожидается объект (dict).")
            return errors
        if DiscoveryConfig.KEY_RECURSIVE_SEARCH not in data:
            errors.append("Discovery: отсутствует поле recursive_search.")
        else:
            val = data[DiscoveryConfig.KEY_RECURSIVE_SEARCH]
            if not isinstance(val, bool):
                errors.append("Discovery: recursive_search должен быть true или false (bool).")
        return errors
