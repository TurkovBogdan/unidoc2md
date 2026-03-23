"""Экран списка проектов: открыть, создать и удалить."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.adapters import ProjectInfo
from src.gui.template.components import ScrollableFrame
from src.gui.template.elements import (
    gui_element_button_primary,
    gui_element_button_secondary,
    gui_element_page_title,
)
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.template.styles import FONT_FAMILY_UI, GUI_CONTENT_WRAPPER, GUI_TOPBAR, PALETTE, UI_FONT_SIZE
from src.gui.utils import open_folder


class ProjectListScreen(BaseGUIScreen):
    """Список проектов: выбор или создание."""

    SCREEN_CODE = "project_list"
    SCREEN_TITLE = "unidoc2md | Список проектов"

    def __init__(
        self,
        parent: ttk.Frame,
        app_root,
        on_open_project,
        *,
        on_settings=None,
        on_model_settings=None,
        app_layout=None,
        on_create_project=None,
        on_delete_project=None,
        **kwargs,
    ) -> None:
        super().__init__(parent, app_root=app_root, app_layout=app_layout, **kwargs)
        self.app_root = app_root
        self.on_open_project = on_open_project
        self.on_settings = on_settings
        self.on_model_settings = on_model_settings
        self.on_create_project = on_create_project
        self.on_delete_project = on_delete_project
        self._projects: list[ProjectInfo] = []
        self._projects_body: ttk.Frame | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self._top_panel()

        ph, pv = GUI_CONTENT_WRAPPER["padding"]
        content_wrap = tk.Frame(self, bg=GUI_CONTENT_WRAPPER["background"])
        content_wrap.pack(fill=tk.BOTH, expand=True, padx=(ph, ph), pady=(0, pv))

        gui_element_page_title(content_wrap, "Проекты")

        scroll_area = ScrollableFrame(content_wrap)
        scroll_area.pack(fill=tk.BOTH, expand=True)
        self._projects_body = scroll_area.content_frame

        self.set_projects([])

    def set_projects(self, projects: list[ProjectInfo]) -> None:
        """Обновить список проектов (вызывается контроллером)."""
        self._projects = list(projects)
        if not self._projects_body:
            return
        for child in self._projects_body.winfo_children():
            child.destroy()
        if not self._projects:
            ttk.Label(self._projects_body, text="Проектов пока нет.", style="Muted.TLabel").pack(
                fill=tk.X, padx=0, pady=12
            )
            return
        for info in self._projects:
            self._build_project_row(info)

    def _top_panel(self) -> None:
        """Верхняя панель с кнопками: добавить проект, настройки, настройка моделей."""
        ph, pv = GUI_TOPBAR["padding"]
        gh, _gv = GUI_TOPBAR["gap"]
        bg = GUI_TOPBAR["background"]
        top_bar = tk.Frame(self, bg=bg)
        top_bar.pack(fill=tk.X, pady=(0, pv))
        left_frame = tk.Frame(top_bar, bg=bg)
        left_frame.pack(side=tk.LEFT, padx=(ph, 0), pady=pv)
        gui_element_button_primary(left_frame, "+ Добавить проект", self._create_project).pack(
            side=tk.LEFT, padx=(0, gh)
        )
        right_frame = tk.Frame(top_bar, bg=bg)
        right_frame.pack(side=tk.RIGHT, padx=(0, ph), pady=pv)
        gui_element_button_secondary(right_frame, "Настройки", self._go_settings).pack(
            side=tk.LEFT, padx=(0, gh)
        )
        gui_element_button_secondary(
            right_frame, "Настройка моделей", self._on_model_settings
        ).pack(side=tk.LEFT)

    def _build_project_row(self, info: ProjectInfo) -> None:
        if not self._projects_body:
            return
        row = tk.Frame(
            self._projects_body,
            bg=PALETTE["bg_elevated"],
            highlightthickness=1,
            highlightbackground=PALETTE["border"],
        )
        row.pack(fill=tk.X, pady=(0, 8))
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=0)
        row.grid_columnconfigure(2, weight=0)
        row.grid_columnconfigure(3, weight=0)

        p = PALETTE
        left = tk.Frame(row, bg=p["bg_elevated"])
        left.grid(row=0, column=0, sticky=tk.W, padx=(12, 8), pady=10)
        name_lbl = tk.Label(
            left, text=info.id, bg=p["bg_elevated"], fg=p["text_primary"], font=(FONT_FAMILY_UI, UI_FONT_SIZE["small"])
        )
        name_lbl.pack(side=tk.LEFT)
        sep = tk.Label(left, text=" | ", bg=p["bg_elevated"], fg=p["text_muted"], font=(FONT_FAMILY_UI, UI_FONT_SIZE["small"]))
        sep.pack(side=tk.LEFT)
        files_lbl = tk.Label(
            left,
            text=self._files_suffix(info.docs_count),
            bg=p["bg_elevated"],
            fg=p["text_muted"],
            font=(FONT_FAMILY_UI, UI_FONT_SIZE["small"]),
        )
        files_lbl.pack(side=tk.LEFT)

        open_btn = gui_element_button_primary(
            row, "Открыть", lambda p=info.path: self._open_project(p)
        )
        open_btn.grid(row=0, column=1, sticky=tk.E, padx=(0, 8), pady=6)

        open_folder_btn = gui_element_button_secondary(
            row, "Открыть папку", lambda p=info.path: open_folder(p)
        )
        open_folder_btn.grid(row=0, column=2, sticky=tk.E, padx=(0, 8), pady=6)

        delete_btn = gui_element_button_secondary(
            row, "Удалить", lambda i=info: self._ask_delete_project(i)
        )
        delete_btn.grid(row=0, column=3, sticky=tk.E, padx=(0, 12), pady=6)

        for widget in (row, left, name_lbl, sep, files_lbl):
            widget.bind("<Double-Button-1>", lambda _e, p=info.path: self._open_project(p))

    @staticmethod
    def _files_suffix(files_count: int) -> str:
        if files_count == 1:
            return "1 файл"
        if files_count == 0:
            return "0 файлов"
        return f"{files_count} файлов"

    def _open_project(self, path) -> None:
        if self.on_open_project:
            self.on_open_project(path)

    def _ask_delete_project(self, info: ProjectInfo) -> None:
        if not self._app_layout:
            if self.on_delete_project:
                self.on_delete_project(info)
            return
        self._app_layout.modals.show_confirm(
            title="Удаление проекта",
            message=(
                f"Удалить проект '{info.id}'?\n\n"
                "Будет удалена вся папка проекта вместе с файлами."
            ),
            on_confirm=lambda: (self.on_delete_project(info) if self.on_delete_project else None),
            confirm_text="Удалить",
            cancel_text="Отмена",
        )

    def _go_settings(self) -> None:
        if self.on_settings:
            self.on_settings()

    def _on_model_settings(self) -> None:
        if self.on_model_settings:
            self.on_model_settings()

    def show_info(
        self,
        title: str,
        message: str,
        *,
        errors: list[str] | None = None,
    ) -> None:
        """Показать оверлей-уведомление (для вызова из app, например «Обновить модели»)."""
        if self._app_layout:
            self._app_layout.modals.show_info(title, message, errors=errors)

    def _create_project(self) -> None:
        if not self._app_layout:
            return
        self._app_layout.modals.show_input(
            title="Новый проект",
            prompt="Имя проекта (папка в projects/):",
            on_submit=self._do_create_project,
            default="",
        )

    def _do_create_project(self, name: str) -> None:
        if self.on_create_project:
            self.on_create_project(name)
