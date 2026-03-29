"""Smoke: main_cli() does not crash; without a project, a warning is emitted."""

import json
from pathlib import Path

import pytest

from src.app import app_root, main_cli
from src.modules.file_extract import get_default_extract_payload
from src.modules.project import ValidationResult
from src.modules.project.project_config import ProjectConfig


def test_main_no_project_warns(capsys, caplog):
    """Without --project, main_cli(None) exits with a warning (stdout/stderr or log)."""
    main_cli(None)
    captured = capsys.readouterr()
    out = (captured.out + captured.err).lower()
    log_text = caplog.text.lower()
    assert (
        "проект" in out or "project" in out or "укажите" in out or "warning" in out
        or "проект" in log_text or "project" in log_text or "укажите" in log_text
    )


def test_main_with_project_runs(tmp_path, monkeypatch):
    """With a project and valid config, main_cli() completes without raising."""
    from src.modules.project.config_io import ensure_project_dirs

    monkeypatch.setattr("src.app.app_root", tmp_path)
    monkeypatch.setattr(
        "src.modules.project.validate_project_config",
        lambda project_root, config_data=None, *, check_tokens=True: ValidationResult(is_valid=True),
    )
    projects = tmp_path / "projects" / "demo"
    ensure_project_dirs(projects)
    (projects / "docs").mkdir(exist_ok=True)
    config = dict(ProjectConfig.create_default_dict())
    config["extract"] = get_default_extract_payload()
    (projects / "config.json").write_text(json.dumps(config), encoding="utf-8")
    main_cli("demo")
    # Smoke: main_cli finished without raising
