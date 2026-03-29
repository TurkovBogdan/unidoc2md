"""ProjectManager invariants: create, delete, list, get/update config, resolve_project_root, directory layout."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.file_extract.providers import PdfExtractProvider
from src.modules.project.config_io import save_project_config
from src.modules.project.manager import ProjectManager
from src.modules.project import (
    ProjectAlreadyExistsError,
    ProjectConfig,
    ProjectDeletePathOutsideError,
    ProjectFolderNotFoundError,
    ProjectInfo,
    PROJECT_CONFIG_KEYS,
    ProjectNameEmptyError,
)


def test_manager_create_creates_project_directory_and_config(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    project_root = manager.create("demo")
    assert project_root == tmp_path / "projects" / "demo"
    assert project_root.is_dir()
    assert (project_root / "docs").is_dir()
    assert (project_root / "cache").is_dir()
    assert (project_root / "result").is_dir()
    assert (project_root / "config.json").exists()


def test_manager_create_empty_name_raises(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    with pytest.raises(ProjectNameEmptyError):
        manager.create("")
    with pytest.raises(ProjectNameEmptyError):
        manager.create("   ")


def test_manager_create_existing_project_raises(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    manager.create("demo")
    with pytest.raises(ProjectAlreadyExistsError):
        manager.create("demo")


def test_manager_delete_removes_project_directory(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    project_root = manager.create("demo")
    assert project_root.is_dir()
    manager.delete(project_root)
    assert not project_root.exists()


def test_manager_delete_outside_projects_raises(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    with pytest.raises(ProjectDeletePathOutsideError):
        manager.delete(tmp_path)
    with pytest.raises(ProjectDeletePathOutsideError):
        manager.delete(tmp_path / "other" / "folder")


def test_manager_delete_missing_folder_raises(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    projects.mkdir(parents=True)
    missing = projects / "ghost"
    manager = ProjectManager(tmp_path)
    with pytest.raises(ProjectFolderNotFoundError):
        manager.delete(missing)


def test_manager_list_projects_returns_empty_when_no_projects(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    assert manager.list_projects() == []


def test_manager_list_projects_returns_created_projects(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    manager.create("one")
    manager.create("two")
    projects = manager.list_projects()
    ids = {p.id for p in projects}
    assert "one" in ids
    assert "two" in ids
    for p in projects:
        assert isinstance(p, ProjectInfo)
        assert p.path.is_dir()


def test_manager_get_config_returns_project_config(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    project_root = manager.create("demo")
    config = manager.get_config(project_root)
    assert isinstance(config, ProjectConfig)
    assert config.project_root == project_root


def test_manager_get_config_dict_returns_dict(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    project_root = manager.create("demo")
    data = manager.get_config_dict(project_root)
    assert isinstance(data, dict)
    assert all(k in data for k in PROJECT_CONFIG_KEYS)


def test_manager_update_config_persists(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    project_root = manager.create("demo")
    new_data = dict(ProjectConfig.create_default_dict())
    new_data["extract"] = dict(new_data["extract"])
    new_data["extract"]["pdf_extract_provider"] = dict(new_data["extract"].get("pdf_extract_provider", {}))
    new_data["extract"]["pdf_extract_provider"]["algorithm"] = PdfExtractProvider.PDF_ALGORITHM_SKIP
    manager.update_config(project_root, new_data)
    config = manager.get_config(project_root)
    pdf_cfg = (config.extract or {}).get("pdf_extract_provider") or {}
    assert pdf_cfg.get("algorithm") == PdfExtractProvider.PDF_ALGORITHM_SKIP


def test_manager_get_project_root_by_name(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    project_root = manager.create("demo")
    found = manager.get_project_root_by_name("demo")
    assert found == project_root
    assert manager.get_project_root_by_name("nonexistent") is None
    assert manager.get_project_root_by_name("") is None


def test_manager_resolve_project_root_single_project(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    project_root = manager.create("only")
    resolved = manager.resolve_project_root()
    assert resolved == project_root


def test_manager_resolve_project_root_no_projects_returns_none(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    assert manager.resolve_project_root() is None


def test_manager_resolve_project_root_multiple_projects_returns_none(tmp_path: Path) -> None:
    manager = ProjectManager(tmp_path)
    manager.create("one")
    manager.create("two")
    assert manager.resolve_project_root() is None
