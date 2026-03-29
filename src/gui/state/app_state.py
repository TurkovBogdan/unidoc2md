"""GUI app state container. Passed via DI, no global singleton."""

from __future__ import annotations

from pathlib import Path


class AppState:
    """Holds app root and current project path. Injected from bootstrap/controllers."""

    def __init__(self, app_root: Path) -> None:
        self.app_root = app_root
        self.current_project: Path | None = None
