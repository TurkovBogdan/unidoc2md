"""Tests for registry_options adapter: OCR/Vision options return lists."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from src.gui.adapters import registry_options


def _mock_available_values(ocr_providers=None, ocr_models=None, vision_providers=None, vision_models=None):
    return SimpleNamespace(
        ocr_providers=ocr_providers or [],
        ocr_models=ocr_models or [],
        vision_providers=vision_providers or [],
        vision_models=vision_models or {},
    )


@patch("src.modules.project.sections.image_processing_config.ImageProcessingConfig.get_available_values")
def test_get_ocr_provider_options_returns_list(mock_get: object) -> None:
    """get_ocr_provider_options returns a list of strings."""
    mock_get.return_value = _mock_available_values(ocr_providers=["a"])
    result = registry_options.get_ocr_provider_options()
    assert isinstance(result, list)
    assert all(isinstance(x, str) for x in result)


@patch("src.modules.project.sections.image_processing_config.ImageProcessingConfig.get_available_values")
def test_get_vision_provider_options_returns_list(mock_get: object) -> None:
    """get_vision_provider_options returns a list of strings."""
    mock_get.return_value = _mock_available_values(vision_providers=["b"])
    result = registry_options.get_vision_provider_options()
    assert isinstance(result, list)
    assert all(isinstance(x, str) for x in result)


@patch("src.modules.project.sections.image_processing_config.ImageProcessingConfig.get_available_values")
def test_get_ocr_models_for_provider_returns_list(mock_get: object) -> None:
    """get_ocr_models_for_provider returns a list of strings."""
    mock_get.return_value = _mock_available_values(ocr_providers=["any"], ocr_models=["m1"])
    result = registry_options.get_ocr_models_for_provider("any")
    assert isinstance(result, list)
    assert all(isinstance(x, str) for x in result)


@patch("src.modules.project.sections.image_processing_config.ImageProcessingConfig.get_available_values")
def test_get_vision_models_for_provider_returns_list(mock_get: object) -> None:
    """get_vision_models_for_provider returns a list of strings."""
    mock_get.return_value = _mock_available_values(
        vision_models={"any": ["v1"]}
    )
    result = registry_options.get_vision_models_for_provider("any")
    assert isinstance(result, list)


@patch("src.modules.project.sections.image_processing_config.ImageProcessingConfig.get_available_values")
def test_vision_options_only_input_image_providers_and_models(mock_get: object) -> None:
    """Image processing tab lists only providers with input_image models and only those models."""
    mock_get.return_value = _mock_available_values(
        vision_providers=["openai"],
        vision_models={"openai": ["gpt-4o", "gpt-4o-mini"]},
    )
    providers = registry_options.get_vision_provider_options()
    assert providers == ["openai"]
    assert registry_options.get_vision_models_for_provider("openai") == ["gpt-4o", "gpt-4o-mini"]
    assert registry_options.get_vision_models_for_provider("anthropic") == []
    assert registry_options.get_vision_models_for_provider("") == []
