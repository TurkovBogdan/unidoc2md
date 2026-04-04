"""Common fixtures for file_extract tests; inputs are files under tests/file-sample."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.modules.file_extract import SourceDocument, build_extract_config


@pytest.fixture
def sample_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "file-sample"


@pytest.fixture
def build_source():
    def _build(path: Path, *, file_hash: str = "h1", mime_type: str | None = None) -> SourceDocument:
        ext = path.suffix.lower()
        return SourceDocument(
            path=str(path),
            folder=".",
            filename=path.name,
            extension=ext,
            mime_type=mime_type,
            file_hash=file_hash,
        )

    return _build


@pytest.fixture
def build_config():
    def _build(project_path: Path, payload: dict | None = None):
        return build_extract_config(project_path, payload or {})

    return _build
