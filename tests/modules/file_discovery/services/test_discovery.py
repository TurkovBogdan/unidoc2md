"""Tests for DiscoveryService: directory, filters, recursion (read-only, no sidecar)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from src.modules.file_discovery import (
    DiscoveredDocument,
    DiscoveryConfig,
    DiscoveryService,
    FileDiscoveryPathNotFoundError,
    SKIP_EXTENSIONS,
)


def test_nonexistent_path_raises() -> None:
    service = DiscoveryService()
    config = DiscoveryConfig(path="/nonexistent/dir/12345", extensions={"*"})
    with pytest.raises(FileDiscoveryPathNotFoundError, match="does not exist"):
        service.discover_files(config)


def test_file_path_raises(tmp_path: Path) -> None:
    (tmp_path / "file.txt").write_text("x")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path / "file.txt"), extensions={"*"})
    with pytest.raises(FileDiscoveryPathNotFoundError, match="not a directory"):
        service.discover_files(config)


def test_empty_dir_returns_empty(tmp_path: Path) -> None:
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    assert service.discover_files(config) == []


def test_extensions_accept_all(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.pdf").write_text("b")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    docs = service.discover_files(config)
    assert len(docs) == 2
    assert {d.filename for d in docs} == {"a", "b"}
    assert all(d.hash is None for d in docs)


def test_extensions_filter(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.pdf").write_text("b")
    (tmp_path / "c.md").write_text("c")
    service = DiscoveryService()
    config = DiscoveryConfig(
        path=str(tmp_path),
        extensions={".txt", ".pdf"},
    )
    docs = service.discover_files(config)
    assert len(docs) == 2
    assert {d.filename for d in docs} == {"a", "b"}


def test_extensions_case_insensitive(tmp_path: Path) -> None:
    (tmp_path / "a.TXT").write_text("a")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={".txt"})
    docs = service.discover_files(config)
    assert len(docs) == 1
    assert docs[0].filename == "a"
    assert docs[0].extension == ".txt"


def test_default_recursive_includes_subdirs(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "root.txt").write_text("r")
    (sub / "nested.txt").write_text("n")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    docs = service.discover_files(config)
    assert len(docs) == 2
    assert {d.filename for d in docs} == {"root", "nested"}


def test_recursive_true(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "root.txt").write_text("r")
    (sub / "nested.txt").write_text("n")
    service = DiscoveryService()
    config = DiscoveryConfig(
        path=str(tmp_path), extensions={"*"}, recursive_search=True
    )
    docs = service.discover_files(config)
    assert len(docs) == 2
    assert {d.filename for d in docs} == {"root", "nested"}


def test_recursive_false(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "root.txt").write_text("r")
    (sub / "nested.txt").write_text("n")
    service = DiscoveryService()
    config = DiscoveryConfig(
        path=str(tmp_path), extensions={"*"}, recursive_search=False
    )
    docs = service.discover_files(config)
    assert len(docs) == 1
    assert docs[0].filename == "root"


def test_skip_extensions_excluded_from_discover(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.md5").write_text("hash")
    (tmp_path / "c.exe").write_text("exe")
    (tmp_path / "d.bat").write_text("bat")
    (tmp_path / "e.sh").write_text("sh")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    docs = service.discover_files(config)
    assert {d.filename for d in docs} == {"a"}
    for ext in SKIP_EXTENSIONS:
        assert not any(d.extension == ext for d in docs)


def test_md5_sidecar_not_in_discover_results(tmp_path: Path) -> None:
    (tmp_path / "f.txt").write_text("hello")
    (tmp_path / "f.txt.md5").write_text("a" * 32)
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    docs = service.discover_files(config)
    assert len(docs) == 1
    assert docs[0].filename == "f"
    assert not any(d.extension == ".md5" for d in docs)


def test_discovered_document_fields(tmp_path: Path) -> None:
    (tmp_path / "doc.pdf").write_text("pdf content")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    docs = service.discover_files(config)
    assert len(docs) == 1
    d = docs[0]
    assert d.path == (tmp_path / "doc.pdf").resolve().as_posix()
    assert d.filename == "doc"
    assert d.extension == ".pdf"
    assert d.mime_type == "application/pdf"
    assert d.hash is None


def test_mime_type_unknown_extension(tmp_path: Path) -> None:
    (tmp_path / "file.xyz").write_text("x")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    docs = service.discover_files(config)
    assert len(docs) == 1
    assert docs[0].mime_type is None
    assert docs[0].extension == ".xyz"


def test_cancel_event_stops_discovery(tmp_path: Path) -> None:
    for i in range(50):
        (tmp_path / f"f{i}.txt").write_text("x")
    service = DiscoveryService()
    config = DiscoveryConfig(
        path=str(tmp_path), extensions={"*"}, recursive_search=False
    )
    cancel = threading.Event()
    cancel.set()
    docs = service.discover_files(config, cancel_event=cancel)
    assert len(docs) == 0


def test_cancel_event_mid_scan(tmp_path: Path) -> None:
    for i in range(20):
        (tmp_path / f"f{i}.txt").write_text("x")
    service = DiscoveryService()
    config = DiscoveryConfig(path=str(tmp_path), extensions={"*"})
    cancel = threading.Event()
    docs_collected: list[DiscoveredDocument] = []

    def run() -> None:
        nonlocal docs_collected
        docs_collected = service.discover_files(config, cancel_event=cancel)

    t = threading.Thread(target=run)
    t.start()
    cancel.set()
    t.join(timeout=2.0)
    assert not t.is_alive()
    assert len(docs_collected) <= 20
