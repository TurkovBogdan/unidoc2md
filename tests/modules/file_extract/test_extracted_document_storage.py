"""Tests for FileExtractCacheService: cache file persistence and ExtractedDocument round-trip."""

from __future__ import annotations

from pathlib import Path

from src.modules.file_discovery.models import DiscoveredDocument
from src.modules.file_extract.services.file_extract_cache import FileExtractCacheService
from src.modules.file_extract.models import (
    ExtractConfig,
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
    SourceDocument,
    compute_extract_hash,
)


def test_save_bytes_writes_to_extract_hash_dir(tmp_path: Path):
    config = ExtractConfig(project_path=tmp_path)
    storage = FileExtractCacheService(config, document_hash="testhash")
    path = storage.save_bytes(b"img1", "doc_p1.png")
    assert path.read_bytes() == b"img1"
    cache_dir = config.cache_dir
    assert path.parent == cache_dir / "testhash"
    assert path.name == "doc_p1.png"
    assert path.suffix == ".png"


def test_save_and_load_extracted_document_roundtrip(tmp_path: Path):
    config = ExtractConfig(project_path=tmp_path)
    source = SourceDocument(
        path=str(tmp_path / "doc.txt"),
        folder=".",
        filename="doc.txt",
        extension=".txt",
        mime_type="text/plain",
        file_hash="abc",
    )
    doc_hash = compute_extract_hash(config, "abc")
    content_path = FileExtractCacheService(config, doc_hash).save_text("Hello", "doc.txt")
    doc = ExtractedDocument(
        source=DiscoveredDocument(
            path=str(source.path),
            folder=source.folder,
            filename=source.filename,
            extension=source.extension,
            mime_type=source.mime_type,
            hash=source.file_hash,
        ),
        config=config,
        extract_hash=doc_hash,
        content=[
            ExtractedDocumentContent(
                content_type="text",
                semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
                path=content_path,
                mime_type="text/plain",
                value="Hello",
            )
        ],
    )
    storage = FileExtractCacheService(config)
    folder = storage.save_extracted_document(doc)
    assert folder == config.cache_dir / doc_hash
    assert (folder / "extracted_document.json").is_file()
    assert (folder / "content.md5").is_file()
    content_hash_from_md5 = (folder / "content.md5").read_text(encoding="utf-8").strip()
    assert len(content_hash_from_md5) == 32 and all(c in "0123456789abcdef" for c in content_hash_from_md5)

    loaded = FileExtractCacheService.load_extracted_document(config, doc_hash)
    assert loaded is not None
    assert loaded.extract_hash == doc.extract_hash
    assert loaded.content_hash is not None
    assert loaded.content_hash == content_hash_from_md5
    assert loaded.source.path == ""
    assert len(loaded.content) == 1
    assert loaded.content[0].content_type == "text"
    assert loaded.content[0].value == "Hello"
    assert loaded.content[0].content_hash is not None
    artifact_md5 = folder / "doc.txt.md5"
    assert artifact_md5.is_file()
    assert artifact_md5.read_text(encoding="utf-8").strip() == loaded.content[0].content_hash


def test_load_extracted_document_missing_returns_none(tmp_path: Path):
    config = ExtractConfig(project_path=tmp_path)
    assert FileExtractCacheService.load_extracted_document(config, "nonexistent_hash") is None


def test_content_lifecycle_replace_and_cache_roundtrip(tmp_path: Path) -> None:
    config = ExtractConfig(project_path=tmp_path)
    doc_hash = compute_extract_hash(config, "img-hash")
    storage = FileExtractCacheService(config, doc_hash)
    image_path = storage.save_bytes(b"image-bytes", "scan.png")
    image_content = ExtractedDocumentContent(
        content_type="image",
        semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
        path=image_path,
        mime_type="image/png",
        content_hash="img-md5",
    )
    text_content = image_content.replace_content(
        content_type="text",
        semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
        path=None,
        mime_type="text/plain",
        content_hash="text-md5",
        value="recognized text",
    )
    doc = ExtractedDocument(
        source=DiscoveredDocument(
            path=str(tmp_path / "docs" / "scan.pdf"),
            folder="docs",
            filename="scan.pdf",
            extension=".pdf",
            mime_type="application/pdf",
            hash="img-hash",
        ),
        config=config,
        extract_hash=doc_hash,
        content=[text_content],
    )
    folder = FileExtractCacheService(config).save_extracted_document(doc)
    loaded = FileExtractCacheService.load_extracted_document(config, doc_hash)
    assert folder == config.cache_dir / doc_hash
    assert loaded is not None
    assert len(loaded.content) == 1
    assert loaded.content[0].semantic_type == SEMANTIC_TYPE_DOCUMENT_FRAGMENT
    assert loaded.content[0].content_type == "text"
    assert loaded.content[0].path is None
    assert loaded.content[0].content_hash == "text-md5"
