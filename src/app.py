"""Application entry: bootstrap via app_bootstrap, then composition."""

from __future__ import annotations

import sys
from pathlib import Path

from src.app_bootstrap import app_bootstrap, app_modules_bootstrap
from src.core.logger import SYSTEM_LOGGER

# Core: directories, app.ini, logger; locales and language from [CORE].LANGUAGE.
app_paths, app_config = app_bootstrap(None)
app_modules_bootstrap((app_paths, app_config))

app_root: Path = app_paths.root


def main_cli(project_name: str | None = None) -> None:
    """CLI entry: resolve project by name and validate its config."""
    if not project_name:
        SYSTEM_LOGGER.warning("Specify project: uv run python main.py --cli --project <name>")
        if getattr(sys, "frozen", False):
            input("Press Enter to exit...")
        return
    from src.modules.project import ProjectManager, validate_project_config

    project_root = ProjectManager(app_root).get_project_root_by_name(project_name)
    if project_root is None:
        SYSTEM_LOGGER.warning(
            "Project not found: %s. Create projects/%s and add docs/ with documents.",
            project_name,
            project_name,
        )
        if getattr(sys, "frozen", False):
            input("Press Enter to exit...")
        return
    validation = validate_project_config(project_root, check_tokens=True)
    if not validation.is_valid:
        for msg in validation.errors:
            SYSTEM_LOGGER.error("Config validation: %s", msg)
        raise ValueError("Project configuration is invalid. Fix errors and run again.")
    SYSTEM_LOGGER.info(
        "Project: %s (config is valid). CLI pipeline is not started.",
        project_root,
    )
    if getattr(sys, "frozen", False):
        input("Press Enter to exit...")


def main_gui(app_root: Path) -> None:
    """Start the GUI configurator. app_root is the app root; GUIBootstrap.init builds Tk root, GUIController.init runs mainloop."""
    from src.gui.bootstrap import GUIBootstrap
    from src.gui.gui_controller import GUIController

    try:
        root = GUIBootstrap.init(app_root)
        GUIController.init(app_root, root)
    except Exception:
        SYSTEM_LOGGER.exception("Critical error while starting GUI")
        raise


__all__ = ["app_config", "app_paths", "app_root", "main_cli", "main_gui"]
