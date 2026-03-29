"""Tests for project config (discovery, extract, image_processing) and config.json validation."""

import json
from pathlib import Path

from src.modules.file_extract import get_default_extract_payload
from src.modules.file_extract.providers import PdfExtractProvider
from src.modules.project import load_project_config, validate_project_config
from src.modules.project.project_config import ProjectConfig


def _canonical_config(extract_overrides=None, discovery_overrides=None, pipeline_overrides=None):
    """Minimal canonical config.json: project, discovery, extract, image_processing, pipeline."""
    base = dict(ProjectConfig.create_default_dict())
    extract = dict(base["extract"])
    if extract_overrides:
        for key, val in extract_overrides.items():
            if key in extract and isinstance(extract[key], dict) and isinstance(val, dict):
                extract[key] = {**extract[key], **val}
            else:
                extract[key] = val
    discovery = dict(base["discovery"])
    if discovery_overrides:
        discovery.update(discovery_overrides)
    pipeline = dict(base["pipeline"])
    if pipeline_overrides:
        pipeline.update(pipeline_overrides)
    return {
        "project": {},
        "discovery": discovery,
        "extract": extract,
        "image_processing": dict(base["image_processing"]),
        "pipeline": pipeline,
    }


def test_config_loads_with_default_extract(tmp_path):
    """Config with default extract loads; extract includes pdf_extract_provider."""
    projects = tmp_path / "projects" / "p"
    projects.mkdir(parents=True)
    (projects / "docs").mkdir()
    config = _canonical_config()
    (projects / "config.json").write_text(json.dumps(config), encoding="utf-8")
    cfg = load_project_config(projects)
    assert "pdf_extract_provider" in (cfg.extract or {})


def test_config_discovery_and_extract_loaded(tmp_path):
    """Config with discovery.recursive_search and extract (pdf) maps into the right fields."""
    projects = tmp_path / "projects" / "p"
    projects.mkdir(parents=True)
    (projects / "docs").mkdir()
    config = _canonical_config(
        discovery_overrides={"recursive_search": False},
        extract_overrides={
            "pdf_extract_provider": {
                "algorithm": PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT,
                "render_scale": "3",
            },
        },
    )
    (projects / "config.json").write_text(json.dumps(config), encoding="utf-8")
    cfg = load_project_config(projects)
    assert cfg.discovery.get("recursive_search") is False
    pdf = (cfg.extract or {}).get("pdf_extract_provider") or {}
    assert pdf.get("algorithm") == PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT
    assert pdf.get("render_scale") == "3"


def test_validate_project_config_rejects_unknown_extract_group_codes(tmp_path):
    """Validator rejects extract with unknown group codes (canonical schema only)."""
    (tmp_path / "config.json").write_text(
        json.dumps({
            "project": {},
            "discovery": {"recursive_search": False},
            "extract": {"unknown_group": {"key": "value"}},
            "image_processing": {},
            "pipeline": {},
        }),
        encoding="utf-8",
    )
    result = validate_project_config(tmp_path, check_tokens=False)
    assert result.is_valid is False
    assert any("Extract:" in e and ("unknown" in e or "group" in e.lower()) for e in result.errors)


def test_validate_project_config_rejects_invalid_extract_field_value(tmp_path):
    """Validator rejects invalid extract field values (e.g. negative int in pdf group)."""
    (tmp_path / "config.json").write_text(
        json.dumps({
            "project": {},
            "discovery": {"recursive_search": False},
            "extract": {
                "pdf_extract_provider": {"enabled": True, "mode": PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT, "min_text_length": -1},
            },
            "image_processing": {},
            "pipeline": {},
        }),
        encoding="utf-8",
    )
    result = validate_project_config(tmp_path, check_tokens=False)
    assert result.is_valid is False
    assert any("Extract:" in e for e in result.errors)
