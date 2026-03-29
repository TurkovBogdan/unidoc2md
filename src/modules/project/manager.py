"""Менеджер проектов: создание, удаление, список, конфигурация, разрешение корня для CLI."""

from __future__ import annotations

import shutil
from pathlib import Path

from .config_io import (
    ensure_project_dirs,
    load_project_config,
    load_project_config_dict,
    save_project_config,
)
from .exceptions import (
    ProjectAlreadyExistsError,
    ProjectDeletePathOutsideError,
    ProjectFolderNotFoundError,
    ProjectNameEmptyError,
)
from .models import ProjectInfo
from .project_config import ProjectConfig
from .project_paths import ProjectPaths


class ProjectManager:
    """Единая точка входа для операций над проектами. Не выполняет discovery/docs_count."""

    def __init__(self, app_root: Path) -> None:
        self._app_root = Path(app_root)
        self._projects_dir = self._app_root / "projects"

    def create(self, name: str) -> Path:
        """Создаёт проект с настройками по умолчанию. Возвращает project_root."""
        name = (name or "").strip()
        if not name:
            raise ProjectNameEmptyError()
        self._projects_dir.mkdir(parents=True, exist_ok=True)
        project_root = self._projects_dir / name
        if project_root.exists():
            raise ProjectAlreadyExistsError()
        project_root.mkdir(parents=True)
        ensure_project_dirs(project_root)
        save_project_config(project_root, ProjectConfig.create_default_dict())
        return project_root

    def delete(self, project_root: Path | str) -> None:
        """Удаляет папку проекта. Путь должен лежать внутри app_root/projects."""
        path = Path(project_root).resolve()
        projects_resolved = self._projects_dir.resolve()
        try:
            path.relative_to(projects_resolved)
        except ValueError:
            raise ProjectDeletePathOutsideError() from None
        if not path.is_dir():
            raise ProjectFolderNotFoundError()
        shutil.rmtree(path)

    def list_projects(self) -> list[ProjectInfo]:
        """Возвращает список проектов (подпапки projects/). docs_count не вычисляется — 0."""
        if not self._projects_dir.is_dir():
            return []
        return [
            ProjectInfo(id=p.name, path=p, docs_count=0)
            for p in self._projects_dir.iterdir()
            if p.is_dir()
        ]

    def update_config(self, project_root: Path, data: dict) -> None:
        """Сохраняет словарь в config.json проекта."""
        save_project_config(Path(project_root), data)

    def get_config(self, project_root: Path) -> ProjectConfig:
        """Возвращает типизированную конфигурацию проекта (ProjectConfig)."""
        return load_project_config(Path(project_root))

    def get_config_dict(self, project_root: Path) -> dict:
        """Возвращает конфигурацию как dict для форм GUI. При отсутствии файла — дефолт."""
        return load_project_config_dict(Path(project_root))

    def get_paths(self, project_root: Path | str) -> ProjectPaths:
        """Возвращает типизированные пути проекта (cache, docs, result, config.json и т.д.)."""
        return ProjectPaths.from_root(Path(project_root))

    def get_project_root_by_name(self, name: str) -> Path | None:
        """Возвращает корень проекта по имени (projects/<name>), если папка существует."""
        if not name or not self._projects_dir.is_dir():
            return None
        path = self._projects_dir / name.strip()
        return path if path.is_dir() else None

    def resolve_project_root(self) -> Path | None:
        """Единственная папка в projects/ (для сценариев с одним проектом). Иначе None."""
        if not self._projects_dir.is_dir():
            return None
        subdirs = [p for p in self._projects_dir.iterdir() if p.is_dir()]
        return subdirs[0] if len(subdirs) == 1 else None
