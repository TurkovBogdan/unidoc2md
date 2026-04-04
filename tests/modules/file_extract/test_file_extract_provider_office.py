"""OfficeExtractProvider: skip, only_text, vision_all, adaptive на эталонных docx/odt из file-sample."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

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
from src.modules.file_extract.providers.types.office_extract.provider import OfficeExtractProvider
from src.modules.file_extract.services.file_extract_cache import FileExtractCacheService


def test_supported_extensions_non_empty() -> None:
    assert len(OfficeExtractProvider.supported_extensions()) > 0


def test_provider_code_declared() -> None:
    assert OfficeExtractProvider.PROVIDER_CODE
    assert OfficeExtractProvider.PROVIDER_CODE == OfficeExtractProvider.provider_code()


# Эталонные документы должны давать осмысленные фрагменты (не обрывки).
_MIN_TEXT_FRAGMENT_CHARS = 256


def _extract(
    tmp_path: Path,
    file_path: Path,
    algorithm: str,
    *,
    file_hash: str = "h_office",
    max_size: int | None = None,
) -> ExtractedDocument:
    ext = file_path.suffix.lower()
    fields: dict = {"algorithm": algorithm}
    if max_size is not None:
        fields["max_size"] = max_size
    config = ExtractConfig(
        project_path=tmp_path,
        provider_configs={
            OfficeExtractProvider.PROVIDER_CODE: fields,
        },
    )
    source = SourceDocument(
        path=str(file_path),
        folder=".",
        filename=file_path.name,
        extension=ext,
        mime_type=None,
        file_hash=file_hash,
    )
    doc_hash = compute_extract_hash(config, source.file_hash)
    storage = FileExtractCacheService(config, doc_hash)
    return OfficeExtractProvider().extract(source, config, storage, document_hash=doc_hash)


def _assert_text_document_fragment_semantics(item: ExtractedDocumentContent) -> None:
    """Офисный текст в extract: носитель text, смысл document_fragment, длина текста ≥ 256 символов."""
    assert item.content_type == CONTENT_TYPE_TEXT
    assert item.semantic_type == SEMANTIC_TYPE_DOCUMENT_FRAGMENT
    body = str(item.value or "").strip()
    assert len(body) >= _MIN_TEXT_FRAGMENT_CHARS, (
        f"ожидалось ≥ {_MIN_TEXT_FRAGMENT_CHARS} значимых символов, получено {len(body)}"
    )


def _assert_text_artifact_materialized(path: Path, *, extract_root: Path) -> None:
    assert path.is_file(), f"файл не создан: {path}"
    assert path.stat().st_size > 0, f"нулевой размер: {path}"
    sidecar = path.with_suffix(path.suffix + ".md5")
    assert sidecar.is_file(), f"нет sidecar хэша: {sidecar}"
    assert sidecar.read_text(encoding="utf-8").strip() != ""
    assert path.resolve().is_relative_to(extract_root.resolve())


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


def _assert_embedded_jpegs_long_edge_at_most(
    doc: ExtractedDocument, *, cap: int, extract_root: Path
) -> None:
    for item in doc.content:
        if item.content_type != CONTENT_TYPE_IMAGE:
            continue
        p = item.path_obj()
        assert p is not None
        _assert_cache_jpeg_materialized(p, extract_root=extract_root)
        with Image.open(p) as img:
            assert max(img.size) <= cap, f"long edge {max(img.size)} > {cap} for {p}"


@pytest.mark.parametrize("filename", ("simple-text.docx", "simple-text.odt"))
def test_office_skip_simple_empty_content(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(tmp_path, file_path, OfficeExtractProvider.OFFICE_ALGORITHM_SKIP)
    assert result.content == []


@pytest.mark.parametrize("filename", ("simple-text.docx", "simple-text.odt"))
def test_office_only_text_simple_single_non_empty_text_part(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_ONLY_TEXT,
        file_hash=f"h_simple_{filename}",
    )
    assert len(result.content) == 1
    item = result.content[0]
    _assert_text_document_fragment_semantics(item)
    out = item.path_obj()
    assert out is not None
    _assert_text_artifact_materialized(out, extract_root=tmp_path / "extract")


@pytest.mark.parametrize("filename", ("text-with-large-images.docx", "text-with-large-images.odt"))
def test_office_only_text_large_images_two_text_parts(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_ONLY_TEXT,
        file_hash=f"h_large_{filename}",
    )
    assert len(result.content) == 2
    for item in result.content:
        _assert_text_document_fragment_semantics(item)
        out = item.path_obj()
        assert out is not None
        _assert_text_artifact_materialized(out, extract_root=tmp_path / "extract")


@pytest.mark.parametrize("filename", ("simple-text.docx", "simple-text.odt"))
def test_office_vision_all_simple_text_single_fragment_semantics(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    """Эталон simple-text без встроенных картинок: одна текстовая часть (≥256, text + document_fragment)."""
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_VISION_ALL,
        file_hash=f"v_simple_{filename}",
    )
    assert len(result.content) == 1
    item = result.content[0]
    _assert_text_document_fragment_semantics(item)
    out = item.path_obj()
    assert out is not None
    _assert_text_artifact_materialized(out, extract_root=tmp_path / "extract")


@pytest.mark.parametrize("filename", ("text-with-large-images.docx", "text-with-large-images.odt"))
def test_office_vision_all_large_images_text_image_alternation(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_VISION_ALL,
        file_hash=f"v_large_{filename}",
    )
    assert len(result.content) == 4
    kinds = [c.content_type for c in result.content]
    assert kinds == [
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
    ]
    extract_root = tmp_path / "extract"
    for ti in (0, 2):
        _assert_text_document_fragment_semantics(result.content[ti])
        tpath = result.content[ti].path_obj()
        assert tpath is not None
        _assert_text_artifact_materialized(tpath, extract_root=extract_root)
    for idx in (1, 3):
        _assert_image_required_detection(result.content[idx])
        img_path = result.content[idx].path_obj()
        assert img_path is not None
        _assert_cache_jpeg_materialized(img_path, extract_root=extract_root)


@pytest.mark.parametrize("filename", ("text-with-small-image.docx", "text-with-small-image.odt"))
def test_office_vision_all_small_image_leading_image_alternation(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    """Порядок: изображение → текст → изображение → текст → изображение."""
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_VISION_ALL,
        file_hash=f"v_small_{filename}",
    )
    assert len(result.content) == 5
    kinds = [c.content_type for c in result.content]
    assert kinds == [
        CONTENT_TYPE_IMAGE,
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
    ]
    extract_root = tmp_path / "extract"
    for ti in (1, 3):
        _assert_text_document_fragment_semantics(result.content[ti])
        tpath = result.content[ti].path_obj()
        assert tpath is not None
        _assert_text_artifact_materialized(tpath, extract_root=extract_root)
    for ii in (0, 2, 4):
        _assert_image_required_detection(result.content[ii])
        img_path = result.content[ii].path_obj()
        assert img_path is not None
        _assert_cache_jpeg_materialized(img_path, extract_root=extract_root)


@pytest.mark.parametrize("filename", ("simple-text.docx", "simple-text.odt"))
def test_office_adaptive_simple_same_as_vision_all(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_ADAPTIVE,
        file_hash=f"ad_simple_{filename}",
    )
    assert len(result.content) == 1
    item = result.content[0]
    _assert_text_document_fragment_semantics(item)
    out = item.path_obj()
    assert out is not None
    _assert_text_artifact_materialized(out, extract_root=tmp_path / "extract")


@pytest.mark.parametrize("filename", ("text-with-large-images.docx", "text-with-large-images.odt"))
def test_office_adaptive_large_images_same_as_vision_all(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_ADAPTIVE,
        file_hash=f"ad_large_{filename}",
    )
    assert len(result.content) == 4
    kinds = [c.content_type for c in result.content]
    assert kinds == [
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
    ]
    extract_root = tmp_path / "extract"
    for ti in (0, 2):
        _assert_text_document_fragment_semantics(result.content[ti])
        tpath = result.content[ti].path_obj()
        assert tpath is not None
        _assert_text_artifact_materialized(tpath, extract_root=extract_root)
    for idx in (1, 3):
        _assert_image_required_detection(result.content[idx])
        img_path = result.content[idx].path_obj()
        assert img_path is not None
        _assert_cache_jpeg_materialized(img_path, extract_root=extract_root)


@pytest.mark.parametrize("filename", ("text-with-small-image.docx", "text-with-small-image.odt"))
def test_office_adaptive_small_image_skips_first_raster_two_images_remain(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    """Первое встроенное изображение ниже порога adaptive не попадает в контент; остаются две картинки (как в vision_all без первой)."""
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_ADAPTIVE,
        file_hash=f"ad_small_{filename}",
    )
    assert len(result.content) == 4
    kinds = [c.content_type for c in result.content]
    assert kinds == [
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
        CONTENT_TYPE_TEXT,
        CONTENT_TYPE_IMAGE,
    ]
    extract_root = tmp_path / "extract"
    for ti in (0, 2):
        _assert_text_document_fragment_semantics(result.content[ti])
        tpath = result.content[ti].path_obj()
        assert tpath is not None
        _assert_text_artifact_materialized(tpath, extract_root=extract_root)
    for ii in (1, 3):
        _assert_image_required_detection(result.content[ii])
        img_path = result.content[ii].path_obj()
        assert img_path is not None
        _assert_cache_jpeg_materialized(img_path, extract_root=extract_root)


@pytest.mark.parametrize("filename", ("text-with-large-images.docx", "text-with-large-images.odt"))
@pytest.mark.parametrize(
    "max_size,expected_long_edge_cap",
    [
        (None, OfficeExtractProvider.DEFAULT_MAX_SIZE),
        (320, 320),
    ],
)
def test_office_max_size_on_embedded_images_default_then_320(
    tmp_path: Path,
    sample_data_dir: Path,
    filename: str,
    max_size: int | None,
    expected_long_edge_cap: int,
) -> None:
    """Настройка max_size: по умолчанию 1440, затем 320 — длинная сторона JPEG не превышает лимит."""
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_VISION_ALL,
        file_hash=f"ms_{expected_long_edge_cap}_{filename.replace('.', '_')}",
        max_size=max_size,
    )
    assert len(result.content) == 4
    extract_root = tmp_path / "extract"
    _assert_embedded_jpegs_long_edge_at_most(
        result, cap=expected_long_edge_cap, extract_root=extract_root
    )
    assert sum(1 for c in result.content if c.content_type == CONTENT_TYPE_IMAGE) == 2


@pytest.mark.parametrize("filename", ("text-with-large-images.docx", "text-with-large-images.odt"))
@pytest.mark.parametrize(
    "max_size,expected_long_edge_cap",
    [
        (None, OfficeExtractProvider.DEFAULT_MAX_SIZE),
        (320, 320),
    ],
)
def test_office_max_size_on_embedded_images_default_then_320(
    tmp_path: Path,
    sample_data_dir: Path,
    filename: str,
    max_size: int | None,
    expected_long_edge_cap: int,
) -> None:
    """Настройка max_size: по умолчанию 1440, затем 320 — длинная сторона JPEG не превышает лимит."""
    file_path = sample_data_dir / "docs" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        OfficeExtractProvider.OFFICE_ALGORITHM_VISION_ALL,
        file_hash=f"ms_{expected_long_edge_cap}_{filename.replace('.', '_')}",
        max_size=max_size,
    )
    assert len(result.content) == 4
    extract_root = tmp_path / "extract"
    _assert_embedded_jpegs_long_edge_at_most(
        result, cap=expected_long_edge_cap, extract_root=extract_root
    )
    assert sum(1 for c in result.content if c.content_type == CONTENT_TYPE_IMAGE) == 2
