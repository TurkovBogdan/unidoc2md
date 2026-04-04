from __future__ import annotations

import threading
from pathlib import Path

from src.modules.file_extract import FileExtractService, SourceDocument
from src.modules.file_extract.models import ExtractConfig


def test_extract_returns_none_for_unknown_extension(tmp_path: Path, build_source) -> None:
    file_path = tmp_path / "data.unknown"
    file_path.write_text("payload", encoding="utf-8")
    service = FileExtractService()
    config = ExtractConfig(project_path=tmp_path)
    result = service.extract(config, build_source(file_path))
    assert result is None


def test_extract_returns_none_when_cancelled_before_start(
    tmp_path: Path, sample_data_dir: Path, build_source
) -> None:
    source_path = sample_data_dir / "text" / "simple-text.txt"
    service = FileExtractService()
    config = ExtractConfig(project_path=tmp_path)
    cancel_event = threading.Event()
    cancel_event.set()
    result = service.extract(config, build_source(source_path), cancel_event=cancel_event)
    assert result is None


def test_extract_routes_to_text_provider_and_returns_content(
    tmp_path: Path, sample_data_dir: Path, build_config, build_source
) -> None:
    source_path = sample_data_dir / "text" / "simple-text.txt"
    service = FileExtractService()
    config = build_config(
        tmp_path,
        {"text_extract_provider": {"algorithm": "only_text"}},
    )
    result = service.extract(config, build_source(source_path))
    assert result is not None
    assert result.source.filename == "simple-text.txt"
    assert len(result.content) == 1
    assert result.content[0].content_type == "text"
    assert result.content[0].value is not None and len(result.content[0].value) > 0


def test_extract_uses_cache_and_refreshes_source_metadata(
    tmp_path: Path, sample_data_dir: Path, build_config
) -> None:
    source_path = sample_data_dir / "text" / "simple-text.txt"
    service = FileExtractService()
    config = build_config(tmp_path, {"text_extract_provider": {"algorithm": "only_text"}})
    first_source = SourceDocument(
        path=str(source_path),
        folder="docs",
        filename="first-name.txt",
        extension=".txt",
        mime_type="text/plain",
        file_hash="same-hash",
    )
    second_source = SourceDocument(
        path=str(source_path),
        folder="other",
        filename="second-name.txt",
        extension=".txt",
        mime_type="text/plain",
        file_hash="same-hash",
    )
    first = service.extract(config, first_source)
    second = service.extract(config, second_source)
    assert first is not None and second is not None
    assert first.extract_hash == second.extract_hash
    assert second.source.folder == "other"
    assert second.source.filename == "second-name.txt"
