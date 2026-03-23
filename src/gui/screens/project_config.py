"""Экран настроек проекта: панель действий, заголовок, табы (файлы, общее/pipeline, extract, …)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.gui.template.components import StyledTabView
from src.gui.template.elements import (
    gui_element_button_primary,
    gui_element_button_secondary,
    gui_element_page_title,
)
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.template.styles import GUI_CONTENT_WRAPPER, GUI_TOPBAR
from src.gui.screens.project import (
    DiscoverySettingsTab,
    ExtractSettingsTab,
    ImageProcessingSettingsTab,
    MarkdownGenerationSettingsTab,
    PipelineSettingsTab,
    TaggingSettingsTab,
)


class ProjectConfigScreen(BaseGUIScreen):
    """Настройки проекта: файлы, общие параметры пайплайна, извлечение, обработка изображений, разметка, теги."""

    SCREEN_CODE = "project_config"
    SCREEN_TITLE = "unidoc2md"

    def __init__(self, parent: ttk.Frame, project_root: Path, on_back, **kwargs) -> None:
        self._project_console = kwargs.pop("project_console", None)
        self._pipeline_storage = kwargs.pop("pipeline_storage", None)
        app_layout = kwargs.pop("app_layout", None)
        self._on_run_project = kwargs.pop("on_run_project", None)
        self.on_save = kwargs.pop("on_save", None)
        self.on_run_click = kwargs.pop("on_run_click", None)
        super().__init__(parent, app_layout=app_layout, **kwargs)
        self.project_root = project_root
        self.on_back = on_back
        self._loaded_project_section: dict = {}
        self._btn_run: ttk.Button | None = None
        self._discovery_tab: DiscoverySettingsTab | None = None
        self._extract_tab: ExtractSettingsTab | None = None
        self._image_processing_tab: ImageProcessingSettingsTab | None = None
        self._markdown_tab: MarkdownGenerationSettingsTab | None = None
        self._tagging_tab: TaggingSettingsTab | None = None
        self._pipeline_tab: PipelineSettingsTab | None = None
        self._build_ui()
        self.bind("<Map>", self._on_screen_show)

    def _build_ui(self) -> None:
        self._top_panel()

        ph, pv = GUI_CONTENT_WRAPPER["padding"]
        content_wrap = tk.Frame(self, bg=GUI_CONTENT_WRAPPER["background"])
        content_wrap.pack(fill=tk.BOTH, expand=True, padx=(ph, ph), pady=(0, pv))

        gui_element_page_title(content_wrap, f"Проект: {self.project_root.name}")

        tabs_spec = [
            ("file_search", "Файлы проекта"),
            ("pipeline_settings", "Общее"),
            ("extract", "Извлечение данных"),
            ("data_processing", "Обработка изображений"),
            ("markdown_generation", "Создание разметки"),
            ("tagging", "Теггирование"),
        ]
        tab_view = StyledTabView(
            content_wrap,
            tabs_spec,
            initial="file_search",
            style="ProjectPanel.TFrame",
            on_tab_change=self._on_project_tab_change,
        )
        tab_view.pack(fill=tk.BOTH, expand=True)

        self._discovery_tab = DiscoverySettingsTab(tab_view.content_holder, self.project_root)
        self._extract_tab = ExtractSettingsTab(tab_view.content_holder, self.project_root)
        self._image_processing_tab = ImageProcessingSettingsTab(tab_view.content_holder, self.project_root)
        self._markdown_tab = MarkdownGenerationSettingsTab(tab_view.content_holder, self.project_root)
        self._tagging_tab = TaggingSettingsTab(tab_view.content_holder, self.project_root)
        self._pipeline_tab = PipelineSettingsTab(tab_view.content_holder, self.project_root)

        tab_view.add_tab_content("file_search", self._discovery_tab)
        tab_view.add_tab_content("pipeline_settings", self._pipeline_tab)
        tab_view.add_tab_content("extract", self._extract_tab)
        tab_view.add_tab_content("data_processing", self._image_processing_tab)
        tab_view.add_tab_content("markdown_generation", self._markdown_tab)
        tab_view.add_tab_content("tagging", self._tagging_tab)

    def _top_panel(self) -> None:
        """Верхняя панель: Вернуться слева; Сохранить и «К выполнению» (экран запуска) справа."""
        ph, pv = GUI_TOPBAR["padding"]
        gh, _gv = GUI_TOPBAR["gap"]
        bg = GUI_TOPBAR["background"]
        top_bar = tk.Frame(self, bg=bg)
        top_bar.pack(fill=tk.X, pady=(0, pv))
        left_frame = tk.Frame(top_bar, bg=bg)
        left_frame.pack(side=tk.LEFT, padx=(ph, 0), pady=pv)
        gui_element_button_secondary(left_frame, "Вернуться", self._go_back).pack(
            side=tk.LEFT, padx=(0, gh)
        )
        right_frame = tk.Frame(top_bar, bg=bg)
        right_frame.pack(side=tk.RIGHT, padx=(0, ph), pady=pv)
        has_run = (
            self._on_run_project is not None
            and self._project_console is not None
            and self._pipeline_storage is not None
        )
        gui_element_button_primary(right_frame, "Сохранить", self._on_save_click).pack(
            side=tk.LEFT, padx=(0, gh) if has_run else 0
        )
        if has_run:
            self._btn_run = gui_element_button_primary(
                right_frame, "К выполнению", self._on_run_click_handler
            )
            self._btn_run.pack(side=tk.LEFT)

    def _on_screen_show(self, event=None) -> None:
        if self._image_processing_tab:
            self._image_processing_tab.refresh_options()
        if self._markdown_tab:
            self._markdown_tab.refresh_options()
        if self._tagging_tab:
            self._tagging_tab.refresh_options()
        if self._discovery_tab:
            self._discovery_tab.refresh_table()

    def _on_project_tab_change(self, tab_id: str) -> None:
        if tab_id == "file_search" and self._discovery_tab:
            self._discovery_tab.refresh_table()

    def load_config_dict(self, data: dict) -> None:
        """Заполняет форму из словаря (вызывается контроллером/application)."""
        self._loaded_project_section = data.get("project") or {}
        discovery = data.get("discovery") or {}
        image_processing = data.get("image_processing") or {}
        pipeline = data.get("pipeline")
        extract = data.get("extract") or {}
        if self._discovery_tab:
            self._discovery_tab.load_discovery(discovery)
        if self._extract_tab:
            self._extract_tab.load_extract(extract)
        if self._image_processing_tab:
            self._image_processing_tab.load_image_processing(image_processing)
        if self._pipeline_tab:
            self._pipeline_tab.load_pipeline(pipeline)
        if self._markdown_tab:
            self._markdown_tab.load_markdown_settings(data.get("markdown"))
        if self._tagging_tab:
            self._tagging_tab.load_tagging_settings(data.get("tagging"))

    def get_form_data(self) -> dict:
        """Возвращает сырые данные формы (нормализацию выполняет application при сохранении)."""
        raw_extract = self._extract_tab.get_raw_extract_payload() if self._extract_tab else {}
        discovery_payload = self._discovery_tab.get_discovery_payload() if self._discovery_tab else {}
        image_data = self._image_processing_tab.get_image_processing_data() if self._image_processing_tab else {}
        pipeline_data = self._pipeline_tab.get_pipeline_data() if self._pipeline_tab else {}
        return {
            "project": self._loaded_project_section,
            "discovery": discovery_payload,
            "extract": raw_extract,
            "image_processing": image_data,
            "markdown": self._markdown_tab.get_markdown_settings_data() if self._markdown_tab else {},
            "tagging": self._tagging_tab.get_tagging_settings_data() if self._tagging_tab else {},
            "pipeline": pipeline_data,
        }

    def _on_save_click(self) -> None:
        if self.on_save:
            self.on_save()

    def _on_run_click_handler(self) -> None:
        if self.on_run_click:
            self.on_run_click()

    def get_screen_title(self) -> str:
        return f"unidoc2md | {self.project_root.name}"

    def _go_back(self) -> None:
        if self.on_back:
            self.on_back()
