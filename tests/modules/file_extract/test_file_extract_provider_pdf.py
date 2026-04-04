"""PdfExtractProvider: skip, only_text, images_always, adaptive на эталонных PDF из file-sample/pdf."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.file_extract.models import (
    CONTENT_TYPE_IMAGE,
    CONTENT_TYPE_TEXT,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
    ExtractConfig,
    ExtractedDocument,
    ExtractedDocumentContent,
    SourceDocument,
    compute_extract_hash,
)
from src.modules.file_extract.providers.types.pdf_extract.provider import PdfExtractProvider
from src.modules.file_extract.services.file_extract_cache import FileExtractCacheService

_MIN_TEXT_FRAGMENT_CHARS = 256


def test_supported_extensions_non_empty() -> None:
    exts = PdfExtractProvider.supported_extensions()
    assert isinstance(exts, set)
    assert len(exts) > 0
    assert exts == {".pdf"}


def test_provider_code_declared() -> None:
    assert PdfExtractProvider.PROVIDER_CODE
    assert PdfExtractProvider.PROVIDER_CODE == PdfExtractProvider.provider_code()


def _extract(
    tmp_path: Path,
    file_path: Path,
    algorithm: str,
    *,
    file_hash: str = "h_pdf",
) -> ExtractedDocument:
    config = ExtractConfig(
        project_path=tmp_path,
        provider_configs={
            PdfExtractProvider.PROVIDER_CODE: {"algorithm": algorithm},
        },
    )
    source = SourceDocument(
        path=str(file_path),
        folder=".",
        filename=file_path.name,
        extension=".pdf",
        mime_type="application/pdf",
        file_hash=file_hash,
    )
    doc_hash = compute_extract_hash(config, source.file_hash)
    storage = FileExtractCacheService(config, doc_hash)
    return PdfExtractProvider().extract(source, config, storage, document_hash=doc_hash)


def _assert_text_document_fragment_semantics(item: ExtractedDocumentContent) -> None:
    assert item.content_type == CONTENT_TYPE_TEXT
    assert item.semantic_type == SEMANTIC_TYPE_DOCUMENT_FRAGMENT
    body = str(item.value or "").strip()
    assert len(body) >= _MIN_TEXT_FRAGMENT_CHARS, (
        f"ожидалось ≥ {_MIN_TEXT_FRAGMENT_CHARS} значимых символов, получено {len(body)}"
    )


def _assert_jpeg_magic(path: Path) -> None:
    data = path.read_bytes()[:3]
    assert data == b"\xff\xd8\xff", f"expected JPEG SOI, got {data!r}"


def _assert_cache_jpeg_materialized(path: Path, *, extract_root: Path) -> None:
    assert path.is_file(), f"файл не создан: {path}"
    assert path.stat().st_size > 0, f"нулевой размер: {path}"
    _assert_jpeg_magic(path)
    sidecar = path.with_suffix(path.suffix + ".md5")
    assert sidecar.is_file(), f"нет sidecar хэша: {sidecar}"
    assert sidecar.read_text(encoding="utf-8").strip() != ""
    assert path.resolve().is_relative_to(extract_root.resolve())


def _assert_image_required_detection(item: ExtractedDocumentContent) -> None:
    assert item.content_type == CONTENT_TYPE_IMAGE
    assert item.semantic_type == SEMANTIC_TYPE_REQUIRED_DETECTION


def _assert_text_artifact_materialized(path: Path, *, extract_root: Path) -> None:
    assert path.is_file(), f"файл не создан: {path}"
    assert path.stat().st_size > 0, f"нулевой размер: {path}"
    sidecar = path.with_suffix(path.suffix + ".md5")
    assert sidecar.is_file(), f"нет sidecar хэша: {sidecar}"
    assert sidecar.read_text(encoding="utf-8").strip() != ""
    assert path.resolve().is_relative_to(extract_root.resolve())


def test_pdf_skip_simple_text_empty_content(tmp_path: Path, sample_data_dir: Path) -> None:
    file_path = sample_data_dir / "pdf" / "simple-text.pdf"
    assert file_path.is_file()
    result = _extract(tmp_path, file_path, PdfExtractProvider.PDF_ALGORITHM_SKIP)
    assert result.content == []


def test_pdf_only_text_simple_text_pages_as_fragments(tmp_path: Path, sample_data_dir: Path) -> None:
    """
    only_text сохраняет текст постранично: непустая страница → один блок.
    В эталоне simple-text.pdf две страницы с текстом — два блока (каждый ≥256, text + document_fragment).
    """
    file_path = sample_data_dir / "pdf" / "simple-text.pdf"
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT,
        file_hash="h_pdf_simple_only_text",
    )
    assert len(result.content) == 2
    assert all(c.content_type == CONTENT_TYPE_TEXT for c in result.content)
    extract_root = tmp_path / "extract"
    for item in result.content:
        _assert_text_document_fragment_semantics(item)
        p = item.path_obj()
        assert p is not None
        _assert_text_artifact_materialized(p, extract_root=extract_root)


def _assert_only_text_two_blocks(tmp_path: Path, sample_data_dir: Path, filename: str, file_hash: str) -> None:
    file_path = sample_data_dir / "pdf" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        PdfExtractProvider.PDF_EXTRACT_MODE_ONLY_TEXT,
        file_hash=file_hash,
    )
    assert len(result.content) == 2
    assert all(c.content_type == CONTENT_TYPE_TEXT for c in result.content)
    extract_root = tmp_path / "extract"
    for item in result.content:
        _assert_text_document_fragment_semantics(item)
        p = item.path_obj()
        assert p is not None
        _assert_text_artifact_materialized(p, extract_root=extract_root)


def test_pdf_only_text_large_images_two_text_blocks(tmp_path: Path, sample_data_dir: Path) -> None:
    _assert_only_text_two_blocks(
        tmp_path, sample_data_dir, "text-with-large-images.pdf", "h_pdf_only_large"
    )


def test_pdf_only_text_small_image_two_text_blocks(tmp_path: Path, sample_data_dir: Path) -> None:
    _assert_only_text_two_blocks(
        tmp_path, sample_data_dir, "text-with-small-image.pdf", "h_pdf_only_small"
    )


@pytest.mark.parametrize(
    "filename",
    ("simple-text.pdf", "text-with-large-images.pdf", "text-with-small-image.pdf"),
)
def test_pdf_images_always_two_pages_two_jpegs_no_text(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    """По странице — JPG; только image/required_detection, без текстовых частей."""
    file_path = sample_data_dir / "pdf" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        PdfExtractProvider.PDF_EXTRACT_MODE_IMAGES_ALWAYS,
        file_hash=f"h_pdf_img_{filename.replace('.', '_')}",
    )
    assert len(result.content) == 2
    assert not any(c.content_type == CONTENT_TYPE_TEXT for c in result.content)
    extract_root = tmp_path / "extract"
    for item in result.content:
        _assert_image_required_detection(item)
        p = item.path_obj()
        assert p is not None
        assert p.suffix.lower() == ".jpg"
        _assert_cache_jpeg_materialized(p, extract_root=extract_root)


def test_pdf_adaptive_adaptive_pdf_text_then_image(
    tmp_path: Path, sample_data_dir: Path
) -> None:
    """adaptive.pdf: страница с нормальным текстом → текст; вторая с крупной графикой → изображение."""
    file_path = sample_data_dir / "pdf" / "adaptive.pdf"
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        PdfExtractProvider.PDF_EXTRACT_MODE_ADAPTIVE,
        file_hash="h_pdf_adaptive_fixture",
    )
    assert len(result.content) == 2
    assert [c.content_type for c in result.content] == [
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
    ]
    extract_root = tmp_path / "extract"
    _assert_text_document_fragment_semantics(result.content[0])
    tp = result.content[0].path_obj()
    assert tp is not None
    _assert_text_artifact_materialized(tp, extract_root=extract_root)
    _assert_image_required_detection(result.content[1])
    jp = result.content[1].path_obj()
    assert jp is not None
    assert jp.suffix.lower() == ".jpg"
    _assert_cache_jpeg_materialized(jp, extract_root=extract_root)
