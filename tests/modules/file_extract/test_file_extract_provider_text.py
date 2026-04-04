"""TextExtractProvider: для файла и настроек вызываем extract и проверяем ExtractedDocument."""

from __future__ import annotations

from pathlib import Path

from src.modules.file_extract.models import (
    CONTENT_TYPE_TEXT,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    ExtractConfig,
    SourceDocument,
    compute_extract_hash,
)
from src.modules.file_extract.providers.types.text_extract_provider import (
    TEXT_ALGORITHM_ONLY_TEXT,
    TEXT_ALGORITHM_SKIP,
    TextExtractProvider,
)
from src.modules.file_extract.services.file_extract_cache import FileExtractCacheService


def test_supported_extensions_non_empty() -> None:
    assert len(TextExtractProvider.supported_extensions()) > 0


def test_provider_code_declared() -> None:
    assert TextExtractProvider.PROVIDER_CODE
    assert TextExtractProvider.PROVIDER_CODE == TextExtractProvider.provider_code()


def test_text_algorithm_skip_returns_empty_document(
    tmp_path: Path, sample_data_dir: Path
) -> None:
    file_path = sample_data_dir / "text" / "simple-text.txt"
    assert file_path.is_file()

    config = ExtractConfig(
        project_path=tmp_path,
        provider_configs={
            TextExtractProvider.provider_code(): {"algorithm": TEXT_ALGORITHM_SKIP},
        },
    )
    source = SourceDocument(
        path=str(file_path),
        folder=".",
        filename=file_path.name,
        extension=".txt",
        mime_type="text/plain",
        file_hash="h1",
    )
    doc_hash = compute_extract_hash(config, source.file_hash)
    storage = FileExtractCacheService(config, doc_hash)

    result = TextExtractProvider().extract(source, config, storage, document_hash=doc_hash)

    assert result.content == []


def test_text_empty_file_has_no_content_parts(tmp_path: Path, sample_data_dir: Path) -> None:
    file_path = sample_data_dir / "text" / "empty.txt"
    assert file_path.is_file()
    assert file_path.read_text(encoding="utf-8") == ""

    config = ExtractConfig(
        project_path=tmp_path,
        provider_configs={
            TextExtractProvider.provider_code(): {"algorithm": TEXT_ALGORITHM_ONLY_TEXT},
        },
    )
    source = SourceDocument(
        path=str(file_path),
        folder=".",
        filename=file_path.name,
        extension=".txt",
        mime_type="text/plain",
        file_hash="h1",
    )
    doc_hash = compute_extract_hash(config, source.file_hash)
    storage = FileExtractCacheService(config, doc_hash)

    result = TextExtractProvider().extract(source, config, storage, document_hash=doc_hash)

    assert result.content == []


def test_text_simple_file_yields_text_document_fragment(
    tmp_path: Path, sample_data_dir: Path
) -> None:
    file_path = sample_data_dir / "text" / "simple-text.txt"
    assert file_path.is_file()

    config = ExtractConfig(
        project_path=tmp_path,
        provider_configs={
            TextExtractProvider.provider_code(): {"algorithm": TEXT_ALGORITHM_ONLY_TEXT},
        },
    )
    source = SourceDocument(
        path=str(file_path),
        folder=".",
        filename=file_path.name,
        extension=".txt",
        mime_type="text/plain",
        file_hash="h1",
    )
    doc_hash = compute_extract_hash(config, source.file_hash)
    storage = FileExtractCacheService(config, doc_hash)

    result = TextExtractProvider().extract(source, config, storage, document_hash=doc_hash)

    assert len(result.content) == 1
    item = result.content[0]
    assert item.content_type == CONTENT_TYPE_TEXT
    assert item.semantic_type == SEMANTIC_TYPE_DOCUMENT_FRAGMENT
    assert item.value is not None and "Well, Prince" in item.value
