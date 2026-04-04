"""Tests for the image_processing section handler (ImageProcessingConfig)."""

from types import SimpleNamespace
from unittest.mock import patch

from src.modules.project.sections.image_processing_config import (
    IMAGE_PROCESSING_DEFAULTS,
    IMAGE_PROCESSING_KEYS,
    IMAGE_PROCESSING_LOGICS,
)


def test_image_processing_logics_defaults_keys() -> None:
    """IMAGE_PROCESSING_LOGICS, IMAGE_PROCESSING_DEFAULTS, IMAGE_PROCESSING_KEYS are defined."""
    L = IMAGE_PROCESSING_LOGICS
    D = IMAGE_PROCESSING_DEFAULTS
    K = IMAGE_PROCESSING_KEYS
    assert L.skip == "skip"
    assert L.vision == "vision"
    assert L.ocr == "ocr"
    assert len(L.options) == 3
    assert L.valid_codes == frozenset({"skip", "vision", "ocr"})
    assert D.ocr_provider == "yandex_ocr"
    assert D.ocr_model == "page"
    assert D.vision_provider == ""
    assert D.vision_model == ""
    assert D.vision_reasoning == "disabled"
    assert D.vision_system_prompt == ""
    assert D.vision_temperature == 0.3
    assert K.text_recognition == "text_recognition"
    assert K.ocr_provider == "ocr_provider"
    assert K.ocr_model == "ocr_model"
    assert K.vision_provider == "vision_provider"
    assert K.vision_model == "vision_model"
    assert K.vision_reasoning == "vision_reasoning"
    assert K.vision_system_prompt == "vision_system_prompt"
    assert K.vision_temperature == "vision_temperature"


def test_get_default_returns_full_dict() -> None:
    """Defaults dict includes every section key."""
    from src.modules.project.sections import ImageProcessingConfig

    default = ImageProcessingConfig.get_default()
    assert isinstance(default, dict)
    assert default[IMAGE_PROCESSING_KEYS.text_recognition] == IMAGE_PROCESSING_LOGICS.skip
    assert default[IMAGE_PROCESSING_KEYS.ocr_provider] == IMAGE_PROCESSING_DEFAULTS.ocr_provider
    assert default[IMAGE_PROCESSING_KEYS.ocr_model] == IMAGE_PROCESSING_DEFAULTS.ocr_model
    assert default[IMAGE_PROCESSING_KEYS.vision_provider] == IMAGE_PROCESSING_DEFAULTS.vision_provider
    assert default[IMAGE_PROCESSING_KEYS.vision_model] == IMAGE_PROCESSING_DEFAULTS.vision_model
    assert default[IMAGE_PROCESSING_KEYS.vision_reasoning] == IMAGE_PROCESSING_DEFAULTS.vision_reasoning
    assert default[IMAGE_PROCESSING_KEYS.vision_system_prompt] == IMAGE_PROCESSING_DEFAULTS.vision_system_prompt
    assert default[IMAGE_PROCESSING_KEYS.vision_temperature] == IMAGE_PROCESSING_DEFAULTS.vision_temperature


def test_validate_valid_data_returns_empty_list() -> None:
    """Valid data produces no validation errors."""
    from src.modules.project.sections import ImageProcessingConfig

    assert ImageProcessingConfig.validate(ImageProcessingConfig.get_default()) == []
    assert ImageProcessingConfig.validate({
        IMAGE_PROCESSING_KEYS.text_recognition: IMAGE_PROCESSING_LOGICS.ocr,
        IMAGE_PROCESSING_KEYS.ocr_provider: IMAGE_PROCESSING_DEFAULTS.ocr_provider,
        IMAGE_PROCESSING_KEYS.ocr_model: IMAGE_PROCESSING_DEFAULTS.ocr_model,
        IMAGE_PROCESSING_KEYS.vision_provider: "",
        IMAGE_PROCESSING_KEYS.vision_model: "",
    }) == []


def test_validate_non_dict_returns_error() -> None:
    """Non-dict input yields a validation error."""
    from src.modules.project.sections import ImageProcessingConfig

    errors = ImageProcessingConfig.validate(None)
    assert len(errors) == 1
    assert "объект" in errors[0] or "dict" in errors[0]


def test_validate_invalid_logic_returns_error() -> None:
    """Invalid text_recognition yields an error."""
    from src.modules.project.sections import ImageProcessingConfig

    errors = ImageProcessingConfig.validate({"text_recognition": "invalid_mode"})
    assert len(errors) == 1
    assert "text_recognition" in errors[0]
    assert "skip" in errors[0] or "ocr" in errors[0]


def test_validate_non_string_field_returns_error() -> None:
    """Non-string provider/model field yields an error."""
    from src.modules.project.sections import ImageProcessingConfig

    errors = ImageProcessingConfig.validate({
        IMAGE_PROCESSING_KEYS.text_recognition: IMAGE_PROCESSING_LOGICS.skip,
        IMAGE_PROCESSING_KEYS.ocr_provider: 123,
    })
    assert len(errors) >= 1
    assert any("ocr_provider" in e or "строкой" in e for e in errors)


def test_validate_invalid_vision_reasoning_returns_error() -> None:
    """Invalid vision_reasoning yields an error."""
    from src.modules.project.sections import ImageProcessingConfig

    errors = ImageProcessingConfig.validate({
        IMAGE_PROCESSING_KEYS.text_recognition: IMAGE_PROCESSING_LOGICS.vision,
        IMAGE_PROCESSING_KEYS.vision_reasoning: "invalid",
    })
    assert len(errors) >= 1
    assert any("vision_reasoning" in e or "disabled" in e for e in errors)


def test_validate_invalid_vision_temperature_returns_error() -> None:
    """Temperature outside 0.0–2.0 or non-numeric yields an error."""
    from src.modules.project.sections import ImageProcessingConfig

    errors = ImageProcessingConfig.validate({
        IMAGE_PROCESSING_KEYS.text_recognition: IMAGE_PROCESSING_LOGICS.vision,
        IMAGE_PROCESSING_KEYS.vision_temperature: 3.0,
    })
    assert len(errors) >= 1
    assert any("vision_temperature" in e or "0.0" in e for e in errors)

    errors2 = ImageProcessingConfig.validate({
        IMAGE_PROCESSING_KEYS.text_recognition: IMAGE_PROCESSING_LOGICS.vision,
        IMAGE_PROCESSING_KEYS.vision_temperature: "x",
    })
    assert len(errors2) >= 1
    assert any("vision_temperature" in e for e in errors2)


@patch("src.modules.project.sections.image_processing_config.locmsg", side_effect=lambda msgid: msgid)
@patch("src.modules.project.sections.image_processing_config.AppConfigStore.get")
@patch("src.modules.llm_models_registry.LLMModelManager")
def test_get_available_values_vision_input_image_models(
    mock_manager_class: object,
    mock_app_config_get: object,
    _mock_locmsg: object,
) -> None:
    """Vision providers/models only with input_image: provider with no such models is omitted."""
    from src.modules.project.sections import ImageProcessingConfig

    # Providers with keys: all reported as available
    mock_lp = SimpleNamespace(is_provider_available=lambda _: True)
    mock_yo = SimpleNamespace(is_available=lambda: False)
    mock_core = SimpleNamespace(debug=False)
    mock_app_config_get.return_value = SimpleNamespace(
        llm_providers=mock_lp,
        yandex_ocr=mock_yo,
        core=mock_core,
    )

    # Registry: openai — one model with input_image; anthropic — only without input_image; xai — empty
    mock_manager = mock_manager_class.return_value
    mock_manager.get_available_models.return_value = [
        {"provider": "openai", "name": "gpt-4o", "enabled": True, "input_image": True},
        {"provider": "openai", "name": "gpt-3.5", "enabled": True, "input_image": False},
        {"provider": "anthropic", "name": "claude-3", "enabled": True, "input_image": False},
    ]

    state = ImageProcessingConfig.get_available_values()

    assert state.vision_providers == ["openai"]
    assert state.vision_models == {"openai": ["gpt-4o"]}
    assert "anthropic" not in state.vision_providers
    assert "xai" not in state.vision_providers
