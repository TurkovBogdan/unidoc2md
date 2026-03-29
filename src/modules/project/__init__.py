"""Управление проектами: создание, конфиг, хранение config.json. Валидация — в config_validation."""

from __future__ import annotations

from .config_io import (
    ensure_project_dirs,
    load_project_config,
    load_project_config_dict,
    save_project_config,
    save_project_config_dict,
)
from .config_validation import ValidationResult, validate_project_config
from .exceptions import (
    ProjectAlreadyExistsError,
    ProjectDeletePathOutsideError,
    ProjectFolderNotFoundError,
    ProjectManagerError,
    ProjectNameEmptyError,
)
from .manager import ProjectManager
from .models import ProjectInfo
from .project_config import PROJECT_CONFIG_KEYS, ProjectConfig
from .project_paths import ProjectPaths
from .sections import ImageProcessingConfig

__all__ = [
    "PROJECT_CONFIG_KEYS",
    "ImageProcessingConfig",
    "ProjectAlreadyExistsError",
    "ProjectConfig",
    "ProjectDeletePathOutsideError",
    "ProjectFolderNotFoundError",
    "ProjectInfo",
    "ProjectManager",
    "ProjectManagerError",
    "ProjectNameEmptyError",
    "ProjectPaths",
    "ValidationResult",
    "ensure_project_dirs",
    "load_project_config",
    "load_project_config_dict",
    "save_project_config",
    "save_project_config_dict",
    "validate_project_config",
]
