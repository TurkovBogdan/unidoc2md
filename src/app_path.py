"""Typed application paths for unidoc2md (built on core ``resolve_runtime_root``)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.core.app_path import resolve_runtime_root
from src.core.filesystem import ensure_dir


@dataclass(frozen=True)
class AppPath:
    """Typed paths for app root and standard directories/files."""

    root: Path
    app_ini: Path
    logs_dir: Path
    system_log: Path
    data_dir: Path
    source_dir: Path
    data_user_dir: Path
    projects_dir: Path
    cache_dir: Path
    temp_dir: Path

    @staticmethod
    def from_root(root: Path | None = None) -> AppPath:
        """Build ``AppPath`` from app root; default ``root=None`` uses ``resolve_runtime_root()``."""
        resolved = Path(root) if root is not None else resolve_runtime_root()
        return AppPath(
            root=resolved,
            app_ini=resolved / "app.ini",
            logs_dir=resolved / "logs",
            system_log=resolved / "logs" / "system.log",
            data_dir=resolved / "data",
            source_dir=resolved / "data" / "source",
            data_user_dir=resolved / "data" / "user",
            projects_dir=resolved / "projects",
            cache_dir=resolved / "cache",
            temp_dir=resolved / "temp",
        )


def ensure_app_runtime_dirs(paths: AppPath) -> None:
    """Create data, projects, and cache dirs (app level; core only ensures ``logs``)."""
    ensure_dir(paths.projects_dir)
    ensure_dir(paths.data_dir)
    ensure_dir(paths.source_dir)
    ensure_dir(paths.data_user_dir)
    ensure_dir(paths.logs_dir)
    ensure_dir(paths.cache_dir)
    ensure_dir(paths.temp_dir)
    ensure_dir(paths.root / "assets" / "locale")


__all__ = ["AppPath", "ensure_app_runtime_dirs"]
