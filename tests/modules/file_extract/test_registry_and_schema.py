from __future__ import annotations

from src.modules.file_extract import get_extract_settings_schema
from src.modules.file_extract.providers.file_extract_provider import (
    get_extension_map,
    get_provider_by_extension,
    get_provider_classes,
    get_provider_settings_groups,
    get_supported_extensions,
)


def test_registry_each_provider_declares_nonempty_provider_code() -> None:
    for provider_cls in get_provider_classes():
        code = getattr(provider_cls, "PROVIDER_CODE", "")
        assert code, f"{provider_cls.__name__} must set non-empty PROVIDER_CODE"
        assert provider_cls.provider_code() == code


def test_registry_contains_all_providers() -> None:
    provider_codes = {provider_cls.provider_code() for provider_cls in get_provider_classes()}
    assert provider_codes == {
        "markdown_extract_provider",
        "pdf_extract_provider",
        "office_extract_provider",
        "text_extract_provider",
        "image_extract_provider",
    }


def test_extension_map_resolves_known_extensions() -> None:
    extension_map = get_extension_map()
    assert extension_map[".pdf"].provider_code() == "pdf_extract_provider"
    assert extension_map[".docx"].provider_code() == "office_extract_provider"
    assert extension_map[".odt"].provider_code() == "office_extract_provider"
    assert extension_map[".txt"].provider_code() == "text_extract_provider"
    assert extension_map[".md"].provider_code() == "markdown_extract_provider"
    assert extension_map[".svg"].provider_code() == "image_extract_provider"


def test_provider_lookup_normalizes_extension() -> None:
    assert get_provider_by_extension("pdf") is not None
    assert get_provider_by_extension(".PDF") is not None
    assert get_provider_by_extension(".missing") is None


def test_supported_extensions_union_contains_core_types() -> None:
    exts = get_supported_extensions()
    assert {".pdf", ".docx", ".odt", ".md", ".txt", ".png", ".svg"} <= exts


def test_settings_groups_match_schema_groups() -> None:
    groups = get_provider_settings_groups()
    schema_groups = get_extract_settings_schema().groups
    assert {g.code for g in schema_groups} == {g.code for g in groups}
    assert all(isinstance(g.title, str) and g.title for g in groups)
    assert all(isinstance(g.description, str) for g in groups)
