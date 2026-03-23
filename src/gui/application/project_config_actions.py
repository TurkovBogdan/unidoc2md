"""Use-case: загрузка, валидация и сохранение конфига проекта."""

from __future__ import annotations

from pathlib import Path

from src.gui.adapters import (
    load_project_config_dict,
    save_project_config_dict,
    validate_config,
)
from src.modules.file_extract import normalize_extract_payload


def get_initial_config(project_root: Path) -> dict:
    """Загружает конфиг проекта и нормализует секцию extract. Для передачи в экран."""
    data = load_project_config_dict(project_root)
    raw_extract = data.get("extract")
    data["extract"] = normalize_extract_payload(raw_extract)
    return data


def validate_and_save(project_root: Path, config_data: dict) -> tuple[bool, list[str]]:
    """
    Нормализует extract, валидирует конфиг и при успехе сохраняет. Возвращает (успех, список ошибок).
    """
    data = dict(config_data)
    data["extract"] = normalize_extract_payload(data.get("extract"))
    is_valid, errors, _ = validate_config(project_root, config_data=data)
    if not is_valid:
        return False, list(errors) if errors else ["Есть ошибки."]
    save_project_config_dict(project_root, data)
    return True, []
