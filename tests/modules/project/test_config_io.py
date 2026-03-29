"""config_io invariants: project creation, read/write config.json, unknown fields, empty/broken config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.modules.file_extract.providers import PdfExtractProvider
from src.modules.project.project_config import PROJECT_CONFIG_KEYS, ProjectConfig
from src.modules.project.config_io import (
    ensure_project_dirs,
    load_project_config,
    load_project_config_dict,
    save_project_config,
    save_project_config_dict,
)


def test_ensure_project_dirs_creates_docs_cache_result_logs(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    assert (tmp_path / "docs").is_dir()
    assert (tmp_path / "cache").is_dir()
    assert (tmp_path / "result").is_dir()
    assert (tmp_path / "logs").is_dir()


def test_load_project_config_when_no_config_returns_defaults(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    config = load_project_config(tmp_path)
    assert config.project_root == tmp_path
    assert "pdf_extract_provider" in (config.extract or {})
    assert config.discovery.get("recursive_search") is False


def test_load_project_config_reads_existing_config(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    data = dict(ProjectConfig.create_default_dict())
    data["extract"] = dict(data["extract"])
    data["extract"]["pdf_extract_provider"] = dict(data["extract"].get("pdf_extract_provider", {}))
    data["extract"]["pdf_extract_provider"]["algorithm"] = PdfExtractProvider.PDF_ALGORITHM_SKIP
    data["extract"]["pdf_extract_provider"]["render_scale"] = "3"
    data["discovery"] = {"recursive_search": True}
    save_project_config(tmp_path, data)
    config = load_project_config(tmp_path)
    pdf_cfg = (config.extract or {}).get("pdf_extract_provider") or {}
    assert pdf_cfg.get("algorithm") == PdfExtractProvider.PDF_ALGORITHM_SKIP
    assert pdf_cfg.get("render_scale") == "3"
    assert config.discovery.get("recursive_search") is True


def test_load_project_config_dict_preserves_project_section(tmp_path: Path) -> None:
    """project section round-trips through load_project_config_dict."""
    ensure_project_dirs(tmp_path)
    data = dict(ProjectConfig.create_default_dict())
    data["project"] = dict(data.get("project", {}))
    data["project"]["custom_key"] = "custom_value"
    data["project"]["nested"] = {"a": 1}
    save_project_config(tmp_path, data)
    loaded = load_project_config_dict(tmp_path)
    assert loaded.get("project", {}).get("custom_key") == "custom_value"
    assert loaded.get("project", {}).get("nested") == {"a": 1}


def test_load_project_config_empty_file_raises(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    (tmp_path / "config.json").write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="config.json пустой"):
        load_project_config(tmp_path)


def test_load_project_config_invalid_json_raises(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    (tmp_path / "config.json").write_text("{ invalid }", encoding="utf-8")
    with pytest.raises(ValueError, match="невалидный JSON"):
        load_project_config(tmp_path)


def test_load_project_config_non_object_json_raises(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    (tmp_path / "config.json").write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="должен быть объектом"):
        load_project_config(tmp_path)


def test_save_project_config_writes_file(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    data = {"key": "value", "nested": {"a": 1}}
    save_project_config(tmp_path, data)
    path = tmp_path / "config.json"
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert all(k in loaded for k in PROJECT_CONFIG_KEYS)
    assert loaded["project"].get("key") == "value"
    assert loaded["project"].get("nested") == {"a": 1}


def test_load_project_config_dict_missing_file_returns_default(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    result = load_project_config_dict(tmp_path)
    assert result == dict(ProjectConfig.create_default_dict())


def test_load_project_config_dict_empty_file_returns_default(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    (tmp_path / "config.json").write_text("", encoding="utf-8")
    result = load_project_config_dict(tmp_path)
    assert all(k in result for k in PROJECT_CONFIG_KEYS)


def test_load_project_config_dict_invalid_json_returns_default(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    (tmp_path / "config.json").write_text("not json", encoding="utf-8")
    result = load_project_config_dict(tmp_path)
    assert all(k in result for k in PROJECT_CONFIG_KEYS)


def test_save_and_load_project_config_dict_roundtrip(tmp_path: Path) -> None:
    ensure_project_dirs(tmp_path)
    data = dict(ProjectConfig.create_default_dict())
    data["project"] = dict(data.get("project", {}))
    data["project"]["extra_field"] = "extra"
    save_project_config_dict(tmp_path, data)
    loaded = load_project_config_dict(tmp_path)
    assert loaded.get("project", {}).get("extra_field") == "extra"


def test_config_json_has_project_discovery_extract_image_processing_pipeline(tmp_path: Path) -> None:
    """config.json keeps project, discovery, extract, image_processing, pipeline. Extract uses group_code -> values."""
    ensure_project_dirs(tmp_path)
    save_project_config(tmp_path, dict(ProjectConfig.create_default_dict()))
    loaded = load_project_config_dict(tmp_path)
    assert all(k in loaded for k in PROJECT_CONFIG_KEYS)
    assert isinstance(loaded["discovery"], dict)
    assert "recursive_search" in loaded["discovery"]
    assert isinstance(loaded["extract"], dict)
    assert "pdf_extract_provider" in loaded["extract"]


def test_extract_payload_preserved_on_save_load(tmp_path: Path) -> None:
    """Extract payload survives config.json save/load. Format: group_code -> values."""
    ensure_project_dirs(tmp_path)
    data = dict(ProjectConfig.create_default_dict())
    data["extract"] = dict(data["extract"])
    data["extract"]["pdf_extract_provider"] = {
        "algorithm": PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT,
        "render_scale": "4",
    }
    save_project_config_dict(tmp_path, data)
    loaded = load_project_config_dict(tmp_path)
    pdf = loaded["extract"].get("pdf_extract_provider", {})
    assert pdf.get("algorithm") == PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT
    assert pdf.get("render_scale") == "4"


def test_discovery_default_and_roundtrip(tmp_path: Path) -> None:
    """Missing discovery defaults recursive_search=False; save/load preserve discovery."""
    ensure_project_dirs(tmp_path)
    (tmp_path / "config.json").write_text(
        json.dumps({
            "project": {},
            "discovery": {},
            "extract": {
                "pdf_extract_provider": {
                    "algorithm": PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT,
                    "render_scale": "2",
                }
            },
            "image_processing": {},
        }),
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    assert config.discovery.get("recursive_search") is False

    data = dict(ProjectConfig.create_default_dict())
    data["discovery"] = {"recursive_search": True}
    save_project_config(tmp_path, data)
    config2 = load_project_config(tmp_path)
    assert config2.discovery.get("recursive_search") is True
    loaded_dict = load_project_config_dict(tmp_path)
    assert loaded_dict.get("discovery", {}).get("recursive_search") is True
