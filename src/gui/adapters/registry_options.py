"""Dropdown options for OCR/Vision from project state (mock only when ``core.debug``)."""

from __future__ import annotations


def _get_ocr_providers() -> list[str]:
    """OCR providers from state (mock only when debug mode is on)."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    return list(state.ocr_providers)


def _get_models(_provider: str, group: str) -> list[str]:
    return ["default"] if group == "multimodal" else []


def get_ocr_provider_options() -> list[str]:
    """OCR provider list from state (mock only in debug)."""
    return _get_ocr_providers()


def get_ocr_models_for_provider(provider: str) -> list[str]:
    """Model codes for the selected OCR provider from state, or a stub list."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    if provider in state.ocr_providers:
        return state.ocr_models
    return _get_models(provider, "multimodal")


def get_vision_provider_options() -> list[str]:
    """Vision (image) providers from state."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    return list(state.vision_providers)


def get_vision_models_for_provider(provider: str) -> list[str]:
    """Vision model codes for the selected provider."""
    from src.modules.project.sections.image_processing_config import ImageProcessingConfig

    state = ImageProcessingConfig.get_available_values()
    return state.vision_models.get(provider, [])


def get_chat_provider_options() -> list[str]:
    """Providers with enabled models suitable for chat (text in / text out)."""
    from src.core import AppConfigStore
    from src.modules.llm_models_registry import LLMModelManager

    manager = LLMModelManager()
    config = AppConfigStore.get()
    providers: set[str] = set()
    for r in manager.get_available_models():
        pc = (r.get("provider") or r.get("provider_code") or "").strip()
        if pc:
            providers.add(pc)
    result = sorted(providers)
    if config.core.debug:
        result = ["mock", *[p for p in result if p != "mock"]]
    return result


def get_chat_models_for_provider(provider: str) -> list[str]:
    """Chat model codes for the selected provider (enabled, any modality)."""
    from src.modules.llm_models_registry import LLMModelManager

    manager = LLMModelManager()
    result = []
    for r in manager.get_available_models():
        pc = (r.get("provider") or r.get("provider_code") or "").strip()
        if pc != provider:
            continue
        name = (r.get("name") or r.get("code") or "").strip()
        if name:
            result.append(name)
    return result
