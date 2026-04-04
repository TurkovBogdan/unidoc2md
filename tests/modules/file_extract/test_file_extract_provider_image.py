"""ImageExtractProvider: алгоритмы, max_size на large-text, все растровые simple-*."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.modules.file_extract.models import (
    CONTENT_TYPE_IMAGE,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
    ExtractConfig,
    ExtractedDocument,
    SourceDocument,
    compute_extract_hash,
)
from src.modules.file_extract.providers.types.image_extract_provider import (
    IMAGE_ALGORITHM_SKIP,
    IMAGE_ALGORITHM_VISION_OCR,
    ImageExtractProvider,
)
from src.modules.file_extract.services.file_extract_cache import FileExtractCacheService


def test_supported_extensions_non_empty() -> None:
    assert len(ImageExtractProvider.supported_extensions()) > 0


def test_provider_code_declared() -> None:
    assert ImageExtractProvider.PROVIDER_CODE
    assert ImageExtractProvider.PROVIDER_CODE == ImageExtractProvider.provider_code()


# Растровые эталоны `simple-*` в file-sample (без .svg).
_SIMPLE_RASTER_FILES: tuple[str, ...] = (
    "simple-png.png",
    "simple-jpg.jpg",
    "simple-jpeg.jpeg",
    "simple-webp.webp",
    "simple-bmp.bmp",
    "simple-gif.gif",
    "simple-tif.tif",
    "simple-tiff.tiff",
)


def _provider_payload(
    algorithm: str,
    *,
    max_size: int | None = None,
) -> dict[str, dict]:
    code = ImageExtractProvider.provider_code()
    fields: dict = {"algorithm": algorithm}
    if max_size is not None:
        fields["max_size"] = max_size
    return {code: fields}


def _extract(
    tmp_path: Path,
    file_path: Path,
    algorithm: str,
    *,
    file_hash: str = "h_img",
    max_size: int | None = None,
) -> ExtractedDocument:
    ext = file_path.suffix.lower()
    config = ExtractConfig(
        project_path=tmp_path,
        provider_configs=_provider_payload(algorithm, max_size=max_size),
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
    return ImageExtractProvider().extract(source, config, storage, document_hash=doc_hash)


def _assert_jpeg_magic(path: Path) -> None:
    data = path.read_bytes()[:3]
    assert data == b"\xff\xd8\xff", f"expected JPEG SOI, got {data!r}"


def _assert_cache_jpeg_materialized(path: Path, *, extract_root: Path) -> None:
    """Артефакт записан на диск: непустой JPEG, sidecar .md5, путь под extract/."""
    assert path.is_file(), f"файл не создан: {path}"
    assert path.stat().st_size > 0, f"нулевой размер: {path}"
    _assert_jpeg_magic(path)
    sidecar = path.with_suffix(path.suffix + ".md5")
    assert sidecar.is_file(), f"нет sidecar хэша: {sidecar}"
    assert sidecar.read_text(encoding="utf-8").strip() != ""
    resolved = path.resolve()
    assert resolved.is_relative_to(extract_root.resolve()), f"не в кэше extract: {path}"


def test_image_skip_returns_empty_content(tmp_path: Path, sample_data_dir: Path) -> None:
    file_path = sample_data_dir / "images" / "large-text.png"
    assert file_path.is_file()
    result = _extract(tmp_path, file_path, IMAGE_ALGORITHM_SKIP)
    assert result.content == []


def test_image_vision_ocr_returns_image_required_detection(tmp_path: Path, sample_data_dir: Path) -> None:
    file_path = sample_data_dir / "images" / "simple-png.png"
    assert file_path.is_file()
    result = _extract(tmp_path, file_path, IMAGE_ALGORITHM_VISION_OCR)
    assert len(result.content) == 1
    item = result.content[0]
    assert item.content_type == CONTENT_TYPE_IMAGE
    assert item.semantic_type == SEMANTIC_TYPE_REQUIRED_DETECTION
    out = item.path_obj()
    assert out is not None
    _assert_cache_jpeg_materialized(out, extract_root=tmp_path / "extract")


@pytest.mark.parametrize("max_size,expected_cap", [(None, 1440), (320, 320)])
def test_image_resize_long_edge_default_then_320(
    tmp_path: Path, sample_data_dir: Path, max_size: int | None, expected_cap: int
) -> None:
    file_path = sample_data_dir / "images" / "large-text.png"
    assert file_path.is_file()
    with Image.open(file_path) as src:
        src_long = max(src.size)

    result = _extract(
        tmp_path,
        file_path,
        IMAGE_ALGORITHM_VISION_OCR,
        file_hash=f"h_large_{expected_cap}",
        max_size=max_size,
    )
    assert len(result.content) == 1
    out = result.content[0].path_obj()
    assert out is not None
    _assert_cache_jpeg_materialized(out, extract_root=tmp_path / "extract")
    with Image.open(out) as jpg:
        out_long = max(jpg.size)
    assert out_long <= expected_cap
    if src_long > expected_cap:
        assert out_long == expected_cap


@pytest.mark.parametrize("filename", _SIMPLE_RASTER_FILES)
def test_image_vision_ocr_simple_raster_formats_non_empty_artifact(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "images" / filename
    assert file_path.is_file()
    result = _extract(
        tmp_path,
        file_path,
        IMAGE_ALGORITHM_VISION_OCR,
        file_hash=f"h_{filename}",
    )
    assert len(result.content) == 1
    item = result.content[0]
    assert item.content_type == CONTENT_TYPE_IMAGE
    assert item.semantic_type == SEMANTIC_TYPE_REQUIRED_DETECTION
    out = item.path_obj()
    assert out is not None
    _assert_cache_jpeg_materialized(out, extract_root=tmp_path / "extract")
