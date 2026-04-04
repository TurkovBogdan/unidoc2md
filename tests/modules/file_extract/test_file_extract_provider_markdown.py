"""MarkdownExtractProvider: сценарии по алгоритмам и эталонным .md из file-sample."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.file_extract.models import (
    CONTENT_TYPE_MARKDOWN,
    CONTENT_TYPE_TEXT,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_MARKDOWN,
    ExtractConfig,
    ExtractedDocument,
    SourceDocument,
    compute_extract_hash,
)
from src.modules.file_extract.providers.types.markdown_extract_provider import (
    MARKDOWN_ALGORITHM_SKIP,
    MARKDOWN_LOGIC_REBUILD_DOCUMENT,
    MARKDOWN_LOGIC_REBUILD_TAGS,
    MARKDOWN_LOGIC_SAVE_AS_IS,
    MarkdownExtractProvider,
)
from src.modules.file_extract.services.file_extract_cache import FileExtractCacheService
from src.modules.markdown.utils.yaml_frontmatter import extract_markdown_yaml


def test_supported_extensions_non_empty() -> None:
    assert len(MarkdownExtractProvider.supported_extensions()) > 0


def test_provider_code_declared() -> None:
    assert MarkdownExtractProvider.PROVIDER_CODE
    assert MarkdownExtractProvider.PROVIDER_CODE == MarkdownExtractProvider.provider_code()


def _extract(
    tmp_path: Path,
    file_path: Path,
    algorithm: str,
    *,
    file_hash: str = "h1",
) -> ExtractedDocument:
    config = ExtractConfig(
        project_path=tmp_path,
        provider_configs={
            MarkdownExtractProvider.provider_code(): {"algorithm": algorithm},
        },
    )
    source = SourceDocument(
        path=str(file_path),
        folder=".",
        filename=file_path.name,
        extension=".md",
        mime_type="text/markdown",
        file_hash=file_hash,
    )
    doc_hash = compute_extract_hash(config, source.file_hash)
    storage = FileExtractCacheService(config, doc_hash)
    return MarkdownExtractProvider().extract(source, config, storage, document_hash=doc_hash)


def test_markdown_skip_simple_is_empty_content(tmp_path: Path, sample_data_dir: Path) -> None:
    file_path = sample_data_dir / "markdown" / "simple-markdown.md"
    assert file_path.is_file()
    result = _extract(tmp_path, file_path, MARKDOWN_ALGORITHM_SKIP)
    assert result.content == []


@pytest.mark.parametrize(
    "algorithm",
    (MARKDOWN_LOGIC_SAVE_AS_IS, MARKDOWN_LOGIC_REBUILD_DOCUMENT),
)
def test_markdown_empty_file_no_content_for_save_or_rebuild_document(
    tmp_path: Path, sample_data_dir: Path, algorithm: str
) -> None:
    file_path = sample_data_dir / "markdown" / "empty.md"
    assert file_path.is_file()
    assert file_path.read_text(encoding="utf-8") == ""

    result = _extract(tmp_path, file_path, algorithm)
    assert result.content == []


def test_markdown_save_as_is_with_tags_keeps_yaml_in_markdown(
    tmp_path: Path, sample_data_dir: Path
) -> None:
    file_path = sample_data_dir / "markdown" / "markdown-with-tags.md"
    assert file_path.is_file()

    result = _extract(tmp_path, file_path, MARKDOWN_LOGIC_SAVE_AS_IS)
    assert len(result.content) == 1
    item = result.content[0]
    assert item.content_type == CONTENT_TYPE_MARKDOWN
    assert item.semantic_type == SEMANTIC_TYPE_MARKDOWN
    assert item.value is not None
    fm = extract_markdown_yaml(item.value)
    assert fm is not None
    assert "tags" in fm
    assert "war-and-peace" in fm["tags"]


def test_markdown_rebuild_tags_with_tags_is_markdown_without_yaml(
    tmp_path: Path, sample_data_dir: Path
) -> None:
    file_path = sample_data_dir / "markdown" / "markdown-with-tags.md"
    assert file_path.is_file()

    result = _extract(tmp_path, file_path, MARKDOWN_LOGIC_REBUILD_TAGS)
    assert len(result.content) == 1
    item = result.content[0]
    assert item.content_type == CONTENT_TYPE_MARKDOWN
    assert item.semantic_type == SEMANTIC_TYPE_MARKDOWN
    assert item.value is not None
    assert extract_markdown_yaml(item.value) is None
    assert "# Title" in item.value


@pytest.mark.parametrize(
    "filename",
    ("markdown-with-tags.md", "simple-markdown.md"),
)
def test_markdown_rebuild_document_text_no_yaml(
    tmp_path: Path, sample_data_dir: Path, filename: str
) -> None:
    file_path = sample_data_dir / "markdown" / filename
    assert file_path.is_file()

    result = _extract(tmp_path, file_path, MARKDOWN_LOGIC_REBUILD_DOCUMENT)
    assert len(result.content) == 1
    item = result.content[0]
    assert item.content_type == CONTENT_TYPE_TEXT
    assert item.semantic_type == SEMANTIC_TYPE_DOCUMENT_FRAGMENT
    assert item.value is not None
    assert extract_markdown_yaml(item.value) is None
    assert "Well, Prince" in item.value
