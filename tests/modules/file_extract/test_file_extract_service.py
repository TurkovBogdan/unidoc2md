"""Tests for FileExtractService: get_supported_extensions, extract, cache, missing provider."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.file_extract import (
    ExtractConfig,
    FileExtractService,
    SourceDocument,
    build_extract_config,
)
from src.modules.file_extract.providers import PdfExtractProvider

# Payload with skip algorithm for PDF.
_PAYLOAD_PDF_SKIP = {
    "pdf_extract_provider": {"algorithm": PdfExtractProvider.PDF_ALGORITHM_SKIP},
}

# Render pages as images — predictable content even for an empty PDF page.
_PAYLOAD_PDF_IMAGES_ALWAYS = {
    "pdf_extract_provider": {
        "algorithm": PdfExtractProvider.PDF_EXTRACT_MODE_IMAGES_ALWAYS,
        "render_scale": "2",
    },
}


def test_get_supported_extensions():
    exts = FileExtractService.get_supported_extensions()
    assert isinstance(exts, set)
    assert ".pdf" in exts
    assert ".txt" in exts


def test_extract_pdf_returns_content(tmp_path: Path):
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    pdf_path = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()
    service = FileExtractService()
    config = build_extract_config(tmp_path, _PAYLOAD_PDF_IMAGES_ALWAYS)
    source = SourceDocument(
        path=str(pdf_path),
        folder=".",
        filename="doc.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        file_hash=None,
    )
    result = service.extract(config, source)
    assert result is not None
    assert result.source.path == source.path
    assert len(result.content) >= 1


def test_extract_unknown_extension_returns_none(tmp_path: Path):
    """For an unknown extension, extract returns None."""
    (tmp_path / "doc.xyz").write_bytes(b"data")
    service = FileExtractService()
    config = ExtractConfig(project_path=tmp_path)
    source = SourceDocument(
        path=str(tmp_path / "doc.xyz"),
        folder=".",
        filename="doc.xyz",
        extension=".xyz",
        mime_type="application/octet-stream",
        file_hash=None,
    )
    result = service.extract(config, source)
    assert result is None


def test_extract_pdf_algorithm_skip_returns_empty_content(tmp_path: Path):
    """With algorithm=skip, provider returns a document with empty content."""
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    pdf_path = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()
    service = FileExtractService()
    config = build_extract_config(tmp_path, _PAYLOAD_PDF_SKIP)
    source = SourceDocument(
        path=str(pdf_path),
        folder=".",
        filename="doc.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        file_hash=None,
    )
    result = service.extract(config, source)
    assert result is not None
    assert result.source.path == source.path
    assert len(result.content) == 0


def test_extract_extension_normalized_without_dot(tmp_path: Path):
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    pdf_path = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()
    service = FileExtractService()
    config = build_extract_config(tmp_path, _PAYLOAD_PDF_IMAGES_ALWAYS)
    source = SourceDocument(
        path=str(pdf_path),
        folder=".",
        filename="doc.pdf",
        extension="pdf",
        mime_type=None,
        file_hash=None,
    )
    result = service.extract(config, source)
    assert result is not None
    assert result.source.extension in (".pdf", "pdf")


def test_extract_cache_hit_returns_cached(tmp_path: Path):
    """A second call for the same document returns the same extract_hash."""
    try:
        import fitz
    except ImportError:
        pytest.skip("PyMuPDF not installed")
    pdf_path = tmp_path / "doc.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(pdf_path)
    doc.close()
    service = FileExtractService()
    config = ExtractConfig(project_path=tmp_path)
    source = SourceDocument(
        path=str(pdf_path),
        folder=".",
        filename="doc.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        file_hash="h1",
    )
    result1 = service.extract(config, source)
    result2 = service.extract(config, source)
    assert result1 is not None and result2 is not None
    assert result1.extract_hash == result2.extract_hash
