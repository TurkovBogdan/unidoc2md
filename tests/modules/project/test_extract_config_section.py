"""Tests for the extract section handler (ExtractConfig in sections)."""

from src.modules.file_extract import get_default_extract_payload
from src.modules.file_extract.providers import PdfExtractProvider
from src.modules.project.sections import ExtractConfig


def test_get_default_returns_dict_from_schema() -> None:
    """Defaults come from provider schema (includes pdf_extract_provider)."""
    default = ExtractConfig.get_default()
    assert isinstance(default, dict)
    assert default == get_default_extract_payload()
    assert "pdf_extract_provider" in default
    assert isinstance(default["pdf_extract_provider"], dict)


def test_validate_valid_payload_returns_empty_list() -> None:
    """Valid schema payload produces no errors."""
    payload = get_default_extract_payload()
    assert ExtractConfig.validate(payload) == []


def test_validate_empty_dict_returns_list() -> None:
    """validate({}) returns a list (schema may require group fields)."""
    errors = ExtractConfig.validate({})
    assert isinstance(errors, list)


def test_validate_non_dict_returns_error() -> None:
    """Non-dict input yields an error."""
    errors = ExtractConfig.validate(None)
    assert len(errors) == 1
    assert "объект" in errors[0] or "dict" in errors[0]
    assert ExtractConfig.validate([]) != []
    assert ExtractConfig.validate("extract") != []


def test_validate_unknown_group_code_returns_error() -> None:
    """Unknown group code yields a validation error."""
    errors = ExtractConfig.validate({"unknown_group": {"key": "value"}})
    assert len(errors) >= 1
    assert "Extract:" in errors[0]
    assert "unknown" in errors[0].lower() or "group" in errors[0].lower()


def test_validate_invalid_field_value_returns_error() -> None:
    """Invalid field value in a group yields an error."""
    payload = {
        "pdf_extract_provider": {
            "enabled": True,
            "mode": PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT,
            "min_text_length": -1,
        },
    }
    errors = ExtractConfig.validate(payload)
    assert len(errors) >= 1
    assert "Extract:" in errors[0]
