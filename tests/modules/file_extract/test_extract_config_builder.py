"""Basic invariants: build_extract_config from normalized payload, runtime extraction for .pdf."""

from __future__ import annotations

from pathlib import Path

from src.modules.file_extract import (
    build_extract_config,
    get_extract_settings_schema,
    normalize_extract_payload,
)
from src.modules.file_extract.models import ExtractConfig
from src.modules.file_extract.providers import PdfExtractProvider


def test_extract_schema_groups_have_title_and_description() -> None:
    """Extract schema groups: title matches provider code; description is str."""
    collection = get_extract_settings_schema()
    for group in collection.groups:
        assert group.title == group.code, f"Group {group.code!r} title must equal code"
        assert isinstance(group.description, str), f"Group {group.code!r} must have description (str)"
    pdf_group = next(g for g in collection.groups if g.code == "pdf_extract_provider")
    assert pdf_group.title == "pdf_extract_provider"


def test_normalize_extract_payload_none_returns_group_based_default() -> None:
    """normalize_extract_payload(None) returns default payload as group_code -> values."""
    payload = normalize_extract_payload(None)
    assert isinstance(payload, dict)
    assert "pdf_extract_provider" in payload
    assert "providers" not in payload


def test_build_extract_config_from_normalized_payload(tmp_path: Path) -> None:
    """build_extract_config builds runtime config from normalized extract payload."""
    payload = normalize_extract_payload(None)
    config = build_extract_config(tmp_path, payload)
    assert isinstance(config, ExtractConfig)
    assert config.project_path == tmp_path
    assert config.provider_configs is not None
    pdf_code = PdfExtractProvider.provider_code()
    algo = config.get_provider_value(pdf_code, "algorithm")
    assert algo in PdfExtractProvider.PDF_ALGORITHMS
    scale = config.get_provider_value(pdf_code, "render_scale")
    assert scale in ("1", "2", "3", "4", "5")


def test_build_extract_config_pdf_skip_algorithm(tmp_path: Path) -> None:
    """Explicit algorithm=skip is preserved in the PDF provider config."""
    payload = normalize_extract_payload({
        "pdf_extract_provider": {"algorithm": PdfExtractProvider.PDF_ALGORITHM_SKIP},
    })
    config = build_extract_config(tmp_path, payload)
    assert (
        config.get_provider_value(PdfExtractProvider.provider_code(), "algorithm")
        == PdfExtractProvider.PDF_ALGORITHM_SKIP
    )
