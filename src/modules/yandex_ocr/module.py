"""yandex_ocr module configuration and runtime state ([YANDEX_OCR] in app.ini, runtime)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces.response_logger import ResponseLoggerProtocol


# Provider id (registries, cache, UI)
PROVIDER_CODE = "yandex_ocr"

# Vision API models: `model` parameter in recognizeText
MODEL_TYPES = (
    "page",
    "page-column-sort",
    "handwritten",
    "table",
    "markdown",
    "math-markdown",
)

DEFAULT_MODEL = "page"


@dataclass(frozen=True)
class YandexOCRConfig:
    """Yandex OCR settings from app.ini (enable flag and API keys)."""

    provider_enabled: bool = False
    key_id: str = ""
    key_secret: str = ""

    def is_available(self) -> bool:
        """True if the provider is enabled and a secret key is set."""
        return bool(self.provider_enabled and (self.key_secret or "").strip())


@dataclass(frozen=True)
class ModuleConfig:
    """Runtime module config: api_config (YandexOCRConfig), cache path (or None), optional API response logger."""

    api_config: YandexOCRConfig
    cache_dir: Path | None
    response_logger: ResponseLoggerProtocol | None = None

    def is_available(self) -> bool:
        """True if the provider is enabled and a secret key is set."""
        return self.api_config.is_available()


class ModuleConfigStore:
    """Single access point for the module runtime configuration."""

    _config: ModuleConfig | None = None

    @classmethod
    def set(cls, config: ModuleConfig) -> None:
        cls._config = config

    @classmethod
    def get(cls) -> ModuleConfig:
        if cls._config is None:
            raise RuntimeError("yandex_ocr module is not initialized")
        return cls._config

    @classmethod
    def reset(cls) -> None:
        cls._config = None


def yandex_ocr_set_api_config(config: YandexOCRConfig) -> None:
    """Update API configuration in the module store (no full restart)."""
    current = ModuleConfigStore.get()
    ModuleConfigStore.set(
        ModuleConfig(
            api_config=config,
            cache_dir=current.cache_dir,
            response_logger=current.response_logger,
        )
    )
