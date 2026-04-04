"""GUI controller: instance class with a static singleton; wires layout, screens, mainloop."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import ClassVar

from src.core import language_choice_required, locmsg
from src.core.logger import SYSTEM_LOGGER
from src.gui.gui_layout import create_gui_layout
from src.gui.state import AppState
from src.gui.controllers import (
    ModelSettingsDetailController,
    ModelSettingsController,
    ProjectConfigController,
    ProjectListController,
    ProjectPipelineController,
    SettingsController,
)
from src.gui.navigation import GUIRouter, ScreenRegistry
from src.gui.screens import LoadingScreen
from src.gui.utils import ProjectPipelineConsole

LOG_PUMP_INTERVAL_MS = 33
LOG_DRAIN_BATCH_SIZE = 100
LOG_MAX_LINES = 2000


class GUIController:
    """Starts GUI, layout, screens, window handlers, mainloop. Access singleton via get()."""

    _instance: ClassVar[GUIController | None] = None

    @classmethod
    def init(cls, app_root: Path, root: tk.Tk) -> None:
        """Create instance, store on cls._instance, call run()."""
        inst = cls(app_root, root)
        cls._instance = inst
        inst.run()

    @classmethod
    def get(cls) -> GUIController:
        """Return the current singleton. Call after init()."""
        if cls._instance is None:
            raise RuntimeError("GUIController is not initialized (call init first)")
        return cls._instance

    def __init__(self, app_root: Path, root: tk.Tk) -> None:
        self._app_root = app_root
        self._root = root
        self._is_closing = False
        self._project_console: ProjectPipelineConsole | None = None
        self._gui_layout = None
        self._registry = ScreenRegistry()
        self._router: GUIRouter | None = None
        self._controllers: dict[str, object] = {}
        self._project_controllers: dict[str, ProjectConfigController] = {}
        self._state: AppState | None = None

    def _on_close(self) -> None:
        """Window close: detach logger, destroy root."""
        self._is_closing = True
        if self._project_console is not None:
            self._project_console.detach_system_logger()
        self._root.destroy()

    def _bind_window_events(self) -> None:
        """Bind window events (close, etc.)."""
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _pump_ui(self) -> None:
        """Timer: flush log queue into the console widget."""
        if self._is_closing or not self._root.winfo_exists():
            return
        if self._project_console is not None:
            self._project_console.drain()
        self._root.after(LOG_PUMP_INTERVAL_MS, self._pump_ui)

    def notify_locale_changed(self) -> None:
        """After set_language: refresh labels on already-built screens."""
        if self._gui_layout is not None:
            try:
                self._gui_layout.console_title_label.configure(
                    text=locmsg("project_execution.console_title")
                )
            except tk.TclError:
                pass
        for key in (
            "project_list",
            "settings",
            "model_settings",
            "model_settings_detail",
            "project_pipeline",
        ):
            ctrl = self._controllers.get(key)
            if ctrl is None:
                continue
            view = getattr(ctrl, "get_frame", lambda: None)()
            if view is not None and hasattr(view, "refresh_locale"):
                try:
                    view.refresh_locale()
                except Exception:
                    SYSTEM_LOGGER.exception("refresh_locale failed for screen %s", key)
        for ctrl in self._project_controllers.values():
            view = getattr(ctrl, "get_frame", lambda: None)()
            if view is not None and hasattr(view, "refresh_locale"):
                try:
                    view.refresh_locale()
                except Exception:
                    SYSTEM_LOGGER.exception("refresh_locale failed for project screen")

    def _show_screen(self, name: str) -> None:
        """Switch visible screen and update window title."""
        if self._router is not None:
            self._router.show_screen(name)

    def _show_project_list(self) -> None:
        """Show project list; refresh if the controller supports it."""
        ctrl = self._controllers.get("project_list")
        if ctrl is not None and hasattr(ctrl, "on_show"):
            ctrl.on_show()
        self._show_screen("project_list")

    def _open_model_settings_detail(self, model_key: str) -> None:
        """Open model edit screen for the given key."""
        ctrl = self._controllers.get("model_settings_detail")
        if ctrl is not None and hasattr(ctrl, "set_model_key"):
            ctrl.set_model_key(model_key)
        self._show_screen("model_settings_detail")

    def _open_project(self, project_root: Path) -> None:
        """Open or create project config screen and switch to it."""
        from src.core import AppConfigStore
        from src.modules.project_pipeline import get_default_storage

        if self._state is None:
            return
        AppConfigStore.load_or_create(self._state.app_root)
        self._state.current_project = project_root
        key = f"project_{project_root}"
        if not self._registry.has(key):
            try:
                controller = ProjectConfigController(
                    self._gui_layout.content_top,
                    project_root,
                    self._gui_layout,
                    on_back=self._show_project_list,
                    on_run_project=self._show_project_pipeline,
                    project_console=self._project_console,
                    pipeline_storage=get_default_storage(),
                )
                self._registry.register(key, controller.get_frame())
                self._project_controllers[key] = controller
            except Exception as exc:
                SYSTEM_LOGGER.exception("Failed to open project %s: %s", project_root, exc)
                self._show_project_list()
                project_list = self._registry.get("project_list")
                if project_list is not None and hasattr(project_list, "show_info"):
                    project_list.show_info(
                        locmsg("gui.error.open_project_title"),
                        "",
                        errors=[str(exc)],
                    )
                return
        else:
            self._project_controllers[key].load_config()
        self._show_screen(key)

    def _show_project_pipeline(self, project_root: Path) -> None:
        """Show execution screen; pipeline runs only from controls on that screen."""
        self._show_screen("project_pipeline")
        ctrl = self._controllers.get("project_pipeline")
        if ctrl is not None and hasattr(ctrl, "set_project"):
            ctrl.set_project(project_root)

    def _setup_layout_and_console(self) -> None:
        """Build layout, log console, router, window events, logger sink."""
        self._gui_layout = create_gui_layout(self._root)
        self._router = GUIRouter(self._gui_layout, self._root, self._registry)
        self._project_console = ProjectPipelineConsole(
            self._gui_layout.log_text,
            max_lines=LOG_MAX_LINES,
            drain_batch_size=LOG_DRAIN_BATCH_SIZE,
        )
        self._project_console.attach_system_logger()
        self._bind_window_events()

    def _build_screens(self) -> None:
        """Create screens and register them."""
        from src.modules.project_pipeline import get_default_storage

        if self._state is None:
            return
        store = self._state
        layout = self._gui_layout

        self._registry.register(
            "loading",
            LoadingScreen(
                layout.loader_slot,
                app_root=store.app_root,
                on_language_ready=lambda: self._show_project_list(),
            ),
        )
        settings_controller = SettingsController(
            layout.content_top,
            store.app_root,
            layout,
            on_back=self._show_project_list,
        )
        self._registry.register("settings", settings_controller.get_frame())
        self._controllers["settings"] = settings_controller

        model_settings_controller = ModelSettingsController(
            layout.content_top,
            store.app_root,
            layout,
            on_back=self._show_project_list,
            on_edit_model=self._open_model_settings_detail,
        )
        self._registry.register("model_settings", model_settings_controller.get_frame())
        self._controllers["model_settings"] = model_settings_controller

        model_settings_detail_controller = ModelSettingsDetailController(
            layout.content_top,
            store.app_root,
            layout,
            on_back=lambda: self._show_screen("model_settings"),
        )
        self._registry.register("model_settings_detail", model_settings_detail_controller.get_frame())
        self._controllers["model_settings_detail"] = model_settings_detail_controller

        project_list_controller = ProjectListController(
            layout.content_top,
            store.app_root,
            layout,
            on_open_project=self._open_project,
            on_settings=lambda: self._show_screen("settings"),
            on_model_settings=lambda: self._show_screen("model_settings"),
        )
        self._registry.register("project_list", project_list_controller.get_frame())
        self._controllers["project_list"] = project_list_controller
        project_pipeline_controller = ProjectPipelineController(
            layout.content_console_top,
            layout,
            on_back=lambda: (
                self._show_screen(f"project_{self._state.current_project}")
                if self._state.current_project is not None
                else self._show_project_list()
            ),
            project_console=self._project_console,
            pipeline_storage=get_default_storage(),
        )
        self._registry.register("project_pipeline", project_pipeline_controller.get_frame())
        self._controllers["project_pipeline"] = project_pipeline_controller

    def _start_ui(self) -> None:
        """Show loading, start log pump; auto-go to projects only if language is set in app.ini."""
        self._show_screen("loading")
        self._root.after(LOG_PUMP_INTERVAL_MS, self._pump_ui)
        if not language_choice_required():
            self._root.after(1000, self._show_project_list)

    def run(self) -> None:
        """Layout, screens, events, mainloop (root already themed in GUIBootstrap.init)."""
        self._state = AppState(self._app_root)

        self._setup_layout_and_console()
        self._build_screens()
        self._start_ui()

        self._root.deiconify()
        try:
            self._root.mainloop()
        except Exception:
            SYSTEM_LOGGER.exception("Error in GUI main loop")
            raise
