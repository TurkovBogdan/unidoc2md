"""Application core: configuration, paths, system logger."""

from src.app_config import AppConfig
from src.app_path import AppPath
from .app_config_builder import AppConfigBuilder
from .app_config_store import AppConfigStore
from .app_locale import (
    AVAILABLE_LANGUAGES,
    add_language_change_listener,
    first_available_language_code,
    language_choice_required,
    locmsg,
    remove_language_change_listener,
    set_language,
)
from .app_path import project_root, resolve_packaged_assets_data_path, resolve_runtime_root

__all__ = [
    "AppConfig",
    "AppConfigBuilder",
    "AppConfigStore",
    "AVAILABLE_LANGUAGES",
    "first_available_language_code",
    "set_language",
    "add_language_change_listener",
    "remove_language_change_listener",
    "language_choice_required",
    "locmsg",
    "AppPath",
    "project_root",
    "resolve_packaged_assets_data_path",
    "resolve_runtime_root",
]
