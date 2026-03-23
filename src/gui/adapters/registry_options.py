"""Опции для выпадающих списков: OCR/Vision из project state (mock только при core.debug)."""

from __future__ import annotations


def _get_ocr_providers() -> list[str]:
    """Провайдеры OCR из state (mock только при включённом режиме отладки)."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    return list(state.ocr_providers)


def _get_models(_provider: str, group: str) -> list[str]:
    return ["default"] if group == "multimodal" else []


def get_ocr_provider_options() -> list[str]:
    """Список провайдеров для OCR из state (mock только при debug)."""
    return _get_ocr_providers()


def get_ocr_models_for_provider(provider: str) -> list[str]:
    """Список кодов моделей для выбранного OCR-провайдера из state или заглушка."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    if provider in state.ocr_providers:
        return state.ocr_models
    return _get_models(provider, "multimodal")


def get_vision_provider_options() -> list[str]:
    """Список провайдеров с vision (image) моделями из state."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    return list(state.vision_providers)


def get_vision_models_for_provider(provider: str) -> list[str]:
    """Список кодов vision-моделей для выбранного провайдера."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    return state.vision_models.get(provider, [])


def get_chat_provider_options() -> list[str]:
    """Список провайдеров с включёнными моделями для чата (текст в/текст из)."""
    from src.modules.llm_models_registry import LLMModelManager

    manager = LLMModelManager()
    providers: set[str] = set()
    for r in manager.get_sorted_records():
        if not r.get("enabled", True):
            continue
        pc = (r.get("provider") or r.get("provider_code") or "").strip()
        if pc:
            providers.add(pc)
    from src.core.app_config_store import AppConfigStore
    config = AppConfigStore.get()
    lp = config.llm_providers
    result = [p for p in sorted(providers) if lp.is_provider_available(p)]
    if config.core.debug:
        result = ["mock", *[p for p in result if p != "mock"]]
    return result


def get_chat_models_for_provider(provider: str) -> list[str]:
    """Список кодов чат-моделей для выбранного провайдера (enabled, любой тип)."""
    from src.modules.llm_models_registry import LLMModelManager

    manager = LLMModelManager()
    result = []
    for r in manager.get_sorted_records():
        if not r.get("enabled", True):
            continue
        pc = (r.get("provider") or r.get("provider_code") or "").strip()
        if pc != provider:
            continue
        name = (r.get("name") or r.get("code") or "").strip()
        if name:
            result.append(name)
    return result
