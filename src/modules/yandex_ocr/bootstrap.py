"""yandex_ocr module bootstrap: populate the module config store."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .module import ModuleConfig, ModuleConfigStore, YandexOCRConfig

if TYPE_CHECKING:
    from .interfaces.response_logger import ResponseLoggerProtocol


def module_yandex_ocr_boot(
    config: YandexOCRConfig,
    *,
    response_logger: ResponseLoggerProtocol | None = None,
    cache_path: Path | str | None = None,
) -> None:
    """
    Primary module init: store config and optional cache dir.
    If cache_path is set: use as ModuleConfig.cache_dir and ensure dir exists.
    If None: cache disabled (caller must pass cache_path in YandexOCRRequest).
    """
    if cache_path is not None:
        cache_path_resolved = Path(cache_path).resolve()
        cache_path_resolved.mkdir(parents=True, exist_ok=True)
    else:
        cache_path_resolved = None
    ModuleConfigStore.set(
        ModuleConfig(
            api_config=config,
            cache_dir=cache_path_resolved,
            response_logger=response_logger,
        )
    )
