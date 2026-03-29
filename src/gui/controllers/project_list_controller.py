"""Controller for the project list (home) screen."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from tkinter import ttk

from src.core import locmsg
from src.core.logger import SYSTEM_LOGGER
from src.gui.adapters import create_project, load_projects, remove_project
from src.gui.controllers.base import BaseScreenController
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.screens.home import ProjectListScreen
from src.modules.project import (
    ProjectAlreadyExistsError,
    ProjectDeletePathOutsideError,
    ProjectFolderNotFoundError,
    ProjectNameEmptyError,
)

if TYPE_CHECKING:
    from src.gui.gui_layout import GUILayout


class ProjectListController(BaseScreenController):
    """Coordinates the home screen: load list, create/delete via adapters."""

    def __init__(
        self,
        parent: ttk.Frame,
        app_root: Path,
        layout: GUILayout,
        *,
        on_open_project,
        on_settings,
        on_model_settings,
    ) -> None:
        self._app_root = app_root
        self._layout = layout
        self._on_open_project = on_open_project
        self._on_settings = on_settings
        self._on_model_settings = on_model_settings
        self._view = ProjectListScreen(
            parent,
            app_root,
            self._on_open_project,
            on_settings=self._on_settings,
            on_model_settings=self._on_model_settings,
            app_layout=layout,
            on_create_project=self._on_create_project,
            on_delete_project=self._on_delete_project,
        )

    @property
    def screen_code(self) -> str:
        return "project_list"

    @property
    def screen_title(self) -> str:
        return self._view.get_screen_title()

    def get_frame(self) -> BaseGUIScreen:
        return self._view

    def on_show(self) -> None:
        try:
            projects = load_projects(self._app_root)
            self._view.refresh_locale()
            self._view.set_projects(projects)
        except Exception as exc:
            SYSTEM_LOGGER.exception("Failed to refresh project list: %s", exc)

    def _on_create_project(self, name: str) -> None:
        name = (name or "").strip()
        if not name:
            return
        try:
            project_root = create_project(self._app_root, name)
            self.on_show()
            if self._on_open_project:
                self._on_open_project(project_root)
        except ProjectAlreadyExistsError:
            if self._layout and self._layout.modals:
                self._layout.modals.show_info(
                    locmsg("home.error.title"),
                    "",
                    errors=[locmsg("home.create.duplicate").format(name=name)],
                )
        except ProjectNameEmptyError:
            if self._layout and self._layout.modals:
                self._layout.modals.show_info(
                    locmsg("home.error.title"),
                    "",
                    errors=[locmsg("error.project_name_empty")],
                )

    def _on_delete_project(self, info) -> None:
        try:
            remove_project(self._app_root, info.path)
            self.on_show()
        except ProjectFolderNotFoundError:
            self.on_show()
            if self._layout and self._layout.modals:
                self._layout.modals.show_info(
                    locmsg("home.delete.status_title"),
                    locmsg("home.delete.already_removed"),
                )
        except ProjectDeletePathOutsideError:
            if self._layout and self._layout.modals:
                self._layout.modals.show_info(
                    locmsg("home.error.title"),
                    "",
                    errors=[locmsg("error.project_delete_path_outside")],
                )
        except Exception as exc:
            if self._layout and self._layout.modals:
                self._layout.modals.show_info(
                    locmsg("home.delete.status_title"),
                    "",
                    errors=[locmsg("home.delete.failed").format(detail=str(exc))],
                )
