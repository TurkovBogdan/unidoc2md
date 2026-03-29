"""Sequential application startup: core, locales, and modules."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.app_config import AppConfig
    from src.app_path import AppPath


def app_bootstrap(root: Path | None = None) -> tuple[AppPath, AppConfig]:
    """
    Same order as unidoc2md startup (see app.py):
    core_boot (directories, app.ini into store, system logger at ``logs/system.log`` and level from config)
    → lang_boot.
    """
    from src.app_config import AppConfig
    from src.core import AppConfigStore
    from src.core.bootstrap import CoreBootstrap
    from src.core.logger import get_system_logger

    app_paths = CoreBootstrap.core_boot(root)
    app_config = AppConfigStore.get()
    CoreBootstrap.lang_boot(
        app_paths,
        {
            "ru": "Русский",
            "en": "English",
            "zh": "中文",
        },
    )
    get_system_logger().info(
        "Bootstrap completed: root=%s, language=%s",
        app_paths.root,
        AppConfigStore.get().core.language,
    )
    return app_paths, app_config


def app_modules_bootstrap(paths_and_config: tuple[AppPath, AppConfig]) -> None:
    """
    Initialize application modules after ``app_bootstrap``: runtime directories,
    register handlers via ``CoreBootstrap.add_module_boot``, then ``modules_boot``.
    """
    app_paths, app_config = paths_and_config

    from src.core.app_path import resolve_packaged_assets_data_path
    from src.core.bootstrap import CoreBootstrap
    from src.core.logger import get_system_logger
    from src.app_path import ensure_app_runtime_dirs
    from src.modules.llm_models_registry.bootstrap import module_llm_model_registry_boot
    from src.modules.llm_providers.bootstrap import module_llm_providers_boot
    from src.modules.yandex_ocr.bootstrap import module_yandex_ocr_boot

    ensure_app_runtime_dirs(app_paths)
    response_logger = get_system_logger() if app_config.core.debug else None

    CoreBootstrap.add_module_boot(
        lambda p: module_llm_model_registry_boot(
            resolve_packaged_assets_data_path("llm_models_registry.json", runtime_root=app_paths.root),
            p.data_user_dir / "llm_models_registry.json",
        )
    )
    CoreBootstrap.add_module_boot(
        lambda p: module_llm_providers_boot(
            config=app_config.llm_providers,
            response_logger=response_logger,
            cache_path=None,
        )
    )
    CoreBootstrap.add_module_boot(
        lambda p: module_yandex_ocr_boot(
            app_config.yandex_ocr,
            response_logger=response_logger,
            cache_path=p.cache_dir / "yandex_ocr",
        )
    )
    CoreBootstrap.modules_boot(app_paths)


__all__ = ["app_bootstrap", "app_modules_bootstrap"]
