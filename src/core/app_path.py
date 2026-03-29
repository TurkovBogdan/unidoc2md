"""Core-level path resolution: model and factory from a root."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Repository root: src/core/app_path.py -> project root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_runtime_root(profile: str | None = None) -> Path:
    """
    Runtime working directory root.
    - Frozen build: directory containing the exe is root; data/, logs/, projects/, etc. live there.
    - Source run: ``project_root / runtime / <profile>``; profile from ``APP_PROFILE`` or ``"dev"``.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    _profile = profile if profile is not None else os.getenv("APP_PROFILE", "dev")
    return _PROJECT_ROOT / "runtime" / _profile


def project_root() -> Path:
    """Repository (project) root."""
    return _PROJECT_ROOT


def resolve_packaged_assets_data_path(file_name: str, *, runtime_root: Path | None = None) -> Path:
    """
    Path to ``assets/data/<file_name>``.

    - Source run: ``<project_root>/assets/data/...``.
    - PyInstaller onefile (``sys.frozen``): if that file exists under ``sys._MEIPASS``, use it
      (bundled via ``datas`` in the .spec); else next to the exe: ``<runtime_root>/assets/data/...``
      (onedir or manual layout).
    """
    name = (file_name or "").strip()
    if not name:
        raise ValueError("file_name must be non-empty")
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "assets" / "data" / name
            if bundled.is_file():
                return bundled
        base = runtime_root if runtime_root is not None else resolve_runtime_root()
        return base / "assets" / "data" / name
    return project_root() / "assets" / "data" / name

