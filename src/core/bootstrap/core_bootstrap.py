"""Core application runtime setup: directories, app.ini, logger. Core vs module boot are explicit."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable, Mapping

from src.core import AppConfigStore
from src.core.app_locale import (
    AVAILABLE_LANGUAGES,
    fallback_language_code,
    resolve_packaged_locale_path,
    set_available_languages,
    set_language_runtime,
)
from src.app_path import AppPath
from src.core.filesystem import ensure_dir
from src.core.logger import DEBUG, SystemLogger, SystemLoggerStore


class CoreBootstrap:
    """
    Register and run handlers during application boot.
    Order: ``core_boot(root)`` loads ``app.ini`` into ``AppConfigStore``; then (after ``get()``)
    ``lang_boot(paths, available_languages)`` — locale dirs and active language from ``[CORE].LANGUAGE``;
    then ``add_module_boot(...)`` and ``modules_boot(paths)``.
    """

    _handlers: list[Callable[[AppPath], None]] = []

    @staticmethod
    def add_module_boot(fn: Callable[[AppPath], None]) -> None:
        """Register a module boot handler invoked from ``modules_boot``. Signature: ``fn(paths: AppPath) -> None``."""
        CoreBootstrap._handlers.append(fn)

    @staticmethod
    def core_boot(root: Path | None = None) -> AppPath:
        """
        Prepare core runtime: logs, app.ini, system logger.
        Does not create module domain files. Safe to call repeatedly.
        Returns ``AppPath`` for ``modules_boot``.
        """
        paths = AppPath.from_root(root)
        ensure_dir(paths.logs_dir)

        SystemLoggerStore.set(
            SystemLogger(logs_dir=paths.logs_dir, file_name="system", level=DEBUG)
        )

        AppConfigStore.load_or_create(paths.root)
        SystemLoggerStore.set_level(AppConfigStore.get().core.log_level)

        return paths

    @staticmethod
    def lang_boot(paths: AppPath, available_languages: Mapping[str, str] | None = None) -> None:
        """
        Register available languages, copy locale JSON into runtime ``assets``,
        apply saved language from ``AppConfigStore`` (``[CORE] LANGUAGE``) if the code is valid;
        otherwise apply fallback locale: ``en`` when available, else first available.
        Language activation here is runtime-only and does not persist to ``app.ini``.
        """
        if available_languages is None:
            raise ValueError("available_languages must be provided")
        set_available_languages(available_languages)
        CoreBootstrap._sync_locale_assets(paths)
        saved = (AppConfigStore.get().core.language or "").strip().lower().replace("-", "_")
        if saved and saved in AVAILABLE_LANGUAGES:
            set_language_runtime(saved)
        else:
            set_language_runtime(fallback_language_code())

    @classmethod
    def modules_boot(cls, paths: AppPath) -> None:
        """Invoke registered module handlers (``add_module_boot``). Call after ``core_boot``."""
        for fn in cls._handlers:
            fn(paths)

    @staticmethod
    def _sync_locale_assets(paths: AppPath) -> None:
        """Copy locale JSON into runtime assets for use after launch."""
        runtime_locale_dir = paths.root / "assets" / "locale"
        ensure_dir(runtime_locale_dir)
        for language in AVAILABLE_LANGUAGES:
            source = resolve_packaged_locale_path(language, runtime_root=paths.root)
            target = runtime_locale_dir / f"{language}.json"
            if not source.is_file():
                continue
            if source.resolve() == target.resolve():
                continue
            shutil.copy2(source, target)


core_boot = CoreBootstrap.core_boot
lang_boot = CoreBootstrap.lang_boot

__all__ = ["CoreBootstrap", "core_boot", "lang_boot"]
