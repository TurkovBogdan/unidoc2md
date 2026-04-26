"""Обработчик секции extract конфигурации проекта: умолчания и валидация по схеме провайдеров."""

from __future__ import annotations

from typing import Any

from src.modules.file_extract import get_default_extract_payload, get_extract_settings_schema
from src.modules.settings_schema.exceptions import SettingsSchemaError


class ExtractConfig:
    """Статический класс для работы с секцией extract (config.json). Умолчания и валидация — по схеме из file_extract."""

    @staticmethod
    def get_default() -> dict[str, Any]:
        """Возвращает extract payload по умолчанию (формат: group_code -> values). Генерируется из схемы провайдеров."""
        return get_default_extract_payload()

    @staticmethod
    def validate(data: Any) -> list[str]:
        """Проверяет данные секции extract по схеме настроек провайдеров. Возвращает список сообщений об ошибках (пустой — данные валидны)."""
        errors: list[str] = []
        if not isinstance(data, dict):
            errors.append("Extract: ожидается объект (dict).")
            return errors
        payload = data
        try:
            get_extract_settings_schema().validate_values(payload)
        except SettingsSchemaError as e:
            errors.append(f"Extract: {e!s}")
        return errors
