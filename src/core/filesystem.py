"""Idempotent helpers to create directories and files at app level (no domain knowledge)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> None:
    """Create the directory and parents if missing."""
    path.mkdir(parents=True, exist_ok=True)


def ensure_text_file(path: Path, content: str) -> None:
    """Create a text file with the given content only if it does not exist yet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def ensure_json_file(path: Path, default_value: Any) -> None:
    """Create a JSON file with the given value only if it does not exist yet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            json.dumps(default_value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
