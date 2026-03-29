"""Global application configuration model (app.ini)."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.models.core_config import CoreConfig
from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.yandex_ocr.module import YandexOCRConfig


@dataclass(frozen=True)
class AppConfig:
    """Full application configuration (source of truth for app.ini)."""

    core: CoreConfig
    llm_providers: LLMProvidersConfig
    yandex_ocr: YandexOCRConfig

    @classmethod
    def default(cls) -> AppConfig:
        """Default config for generating the app.ini template."""
        return cls(
            core=CoreConfig(),
            llm_providers=LLMProvidersConfig(),
            yandex_ocr=YandexOCRConfig(),
        )
