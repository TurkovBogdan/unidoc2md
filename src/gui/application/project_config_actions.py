"""Use case: load, validate, and save project config."""

from __future__ import annotations

from pathlib import Path

from src.gui.adapters import (
    load_project_config_dict,
    save_project_config_dict,
    validate_config,
)
from src.modules.file_extract import normalize_extract_payload


def get_initial_config(project_root: Path) -> dict:
    """Load project config and normalize the ``extract`` section for the editor screen."""
    data = load_project_config_dict(project_root)
    raw_extract = data.get("extract")
    data["extract"] = normalize_extract_payload(raw_extract)
    return data


def validate_and_save(project_root: Path, config_data: dict) -> tuple[bool, list[str]]:
    """Normalize ``extract``, validate config, and save on success. Returns ``(ok, errors)``."""
    data = dict(config_data)
    data["extract"] = normalize_extract_payload(data.get("extract"))
    is_valid, errors, _ = validate_config(project_root, config_data=data)
    if not is_valid:
        return False, list(errors) if errors else ["Validation failed."]
    save_project_config_dict(project_root, data)
    return True, []
