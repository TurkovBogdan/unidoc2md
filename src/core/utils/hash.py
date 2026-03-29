"""Hashing: MD5 of a string and of a file by path."""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK_SIZE = 65536


def md5_string(s: str, encoding: str = "utf-8") -> str:
    """MD5 digest of a string; default encoding utf-8."""
    return hashlib.md5(s.encode(encoding)).hexdigest()


def md5_bytes(data: bytes) -> str:
    """MD5 digest of raw bytes."""
    return hashlib.md5(data).hexdigest()


def md5_file(path: Path | str) -> str:
    """MD5 digest of file contents (read in binary chunks)."""
    path = Path(path) if isinstance(path, str) else path
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


__all__ = ["md5_string", "md5_bytes", "md5_file"]
