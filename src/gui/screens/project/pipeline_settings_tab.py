"""Таб «Общее»: потоки extract, image_processing, markdown, tagging, плашка про OCR."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from src.modules.project.sections.pipeline_config import (
    CREATE_DOCUMENTS_INDEX_DEFAULT,
    EXTRACT_THREADS_MAX,
    EXTRACT_THREADS_MIN,
    IMAGE_PROCESSING_THREADS_MAX,
    IMAGE_PROCESSING_THREADS_MIN,
    KEY_CREATE_DOCUMENTS_INDEX,
    KEY_DISCOVERY_THREADS,
    KEY_EXTRACT_THREADS,
    KEY_IMAGE_PROCESSING_THREADS,
    KEY_MARKDOWN_THREADS,
    KEY_TAGGING_THREADS,
    MARKDOWN_THREADS_MAX,
    MARKDOWN_THREADS_MIN,
    TAGGING_THREADS_MAX,
    TAGGING_THREADS_MIN,
    PIPELINE_HELP_ARTICLE,
    PIPELINE_SETTINGS_UI,
    PipelineConfig,
)
from src.modules.project.sections.tagging_config import TAGGING_BOOL_UI_VALUES, TaggingConfig

from src.gui.template.components import CustomScrollbar, ScrollableFrame, SettingsBlock
from src.gui.template.elements import (
    gui_element_header_3,
    gui_element_input_description,
    gui_element_input_label,
    gui_element_input_select,
    gui_element_input_spin,
    gui_element_separator,
    gui_element_warning_banner,
)
from src.gui.template.styles import (
    FONT_FAMILY_UI,
    PALETTE,
    UI_FONT_SIZE,
    UI_SETTINGS_BLOCK,
    UI_TABS,
)


class PipelineSettingsTab(ttk.Frame):
    """Общие параметры пайплайна: спинбоксы потоков этапов, информационная плашка про OCR."""

    SETTINGS_WIDTH_PX = 520
    _SEPARATOR_PADX = 12

    @staticmethod
    def _bool_to_display(b: bool) -> str:
        return TAGGING_BOOL_UI_VALUES[0] if b else TAGGING_BOOL_UI_VALUES[1]

    @staticmethod
    def _display_to_bool(display: str, default: bool) -> bool:
        d = (display or "").strip()
        if d == TAGGING_BOOL_UI_VALUES[0]:
            return True
        if d == TAGGING_BOOL_UI_VALUES[1]:
            return False
        return default

    def __init__(self, parent: ttk.Frame, project_root: Path, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._project_root = project_root
        self._create_documents_index_var = tk.StringVar(
            value=self._bool_to_display(CREATE_DOCUMENTS_INDEX_DEFAULT)
        )
        self._extract_threads_var = tk.StringVar(value="4")
        self._image_processing_threads_var = tk.StringVar(value="4")
        self._markdown_threads_var = tk.StringVar(value="4")
        self._tagging_threads_var = tk.StringVar(value="4")
        self._build_ui()

    def _build_ui(self) -> None:
        padx, pady = UI_TABS["content_padding"]
        wrap = ttk.Frame(self)
        wrap.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)

        left_frame = tk.Frame(wrap, width=self.SETTINGS_WIDTH_PX, bg=PALETTE["bg_surface"])
        left_frame.pack_propagate(False)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))
        self._scroll = ScrollableFrame(left_frame)
        self._scroll.pack(fill=tk.BOTH, expand=True, padx=(0, self._SEPARATOR_PADX))

        sep = tk.Frame(wrap, width=1, bg=PALETTE["border"], highlightthickness=0)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))
        sep.pack_propagate(False)

        right_frame = tk.Frame(wrap, bg=PALETTE["bg_surface"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        ui = PIPELINE_SETTINGS_UI
        article_label = ttk.Label(
            right_frame,
            text=ui.help_sidebar_title,
            style="RightPanelTitle.TLabel",
        )
        article_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        article_container = tk.Frame(right_frame, bg=PALETTE["bg_surface"])
        article_container.grid(row=1, column=0, sticky=tk.NSEW)
        article_container.columnconfigure(0, weight=1)
        article_container.rowconfigure(0, weight=1)
        self._article_text = tk.Text(
            article_container,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=(FONT_FAMILY_UI, UI_FONT_SIZE["small"]),
            bg=PALETTE["bg_surface"],
            fg=PALETTE["text_muted"],
            insertbackground=PALETTE["text_muted"],
            selectbackground=PALETTE["select_bg"],
            selectforeground=PALETTE["select_fg"],
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
        )
        self._article_scrollbar = CustomScrollbar(
            article_container, command=self._article_text.yview
        )
        self._article_text.configure(yscrollcommand=self._article_scrollbar.set)
        self._article_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._article_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._article_text.configure(state=tk.NORMAL)
        self._article_text.insert(tk.END, PIPELINE_HELP_ARTICLE)
        self._article_text.configure(state=tk.DISABLED)

        cfg = UI_SETTINGS_BLOCK
        block = SettingsBlock(self._scroll.content_frame)

        idx_row = block.add_field_row_frame()
        idx_combo = gui_element_input_select(
            idx_row,
            variable=self._create_documents_index_var,
            values=list(TAGGING_BOOL_UI_VALUES),
            width=28,
        )
        block.finish_field_row(
            idx_row,
            gui_element_input_label(
                idx_row,
                ui.create_documents_index_label,
                wraplength=cfg["column_label_px"],
            ),
            idx_combo,
        )
        block.add_comment(
            gui_element_input_description(
                block.form,
                ui.create_documents_index_hint,
                wraplength=cfg["container_width_px"],
            )
        )

        block.add_full_width_row(gui_element_separator(block.form))
        block.add_comment(
            gui_element_header_3(block.form, ui.threads_section_title, pack=False)
        )

        ex_row = block.add_field_row_frame()
        self._extract_threads_spin = gui_element_input_spin(
            ex_row,
            textvariable=self._extract_threads_var,
            from_=EXTRACT_THREADS_MIN,
            to=EXTRACT_THREADS_MAX,
            width=6,
        )
        block.finish_field_row(
            ex_row,
            gui_element_input_label(
                ex_row, ui.extract_threads_label, wraplength=cfg["column_label_px"]
            ),
            self._extract_threads_spin,
        )
        block.add_comment(
            gui_element_input_description(
                block.form, ui.extract_threads_hint, wraplength=cfg["container_width_px"]
            )
        )

        img_row = block.add_field_row_frame()
        self._image_processing_threads_spin = gui_element_input_spin(
            img_row,
            textvariable=self._image_processing_threads_var,
            from_=IMAGE_PROCESSING_THREADS_MIN,
            to=IMAGE_PROCESSING_THREADS_MAX,
            width=6,
        )
        block.finish_field_row(
            img_row,
            gui_element_input_label(
                img_row,
                ui.image_processing_threads_label,
                wraplength=cfg["column_label_px"],
            ),
            self._image_processing_threads_spin,
        )
        block.add_comment(
            gui_element_input_description(
                block.form,
                ui.image_processing_threads_hint,
                wraplength=cfg["container_width_px"],
            )
        )

        md_row = block.add_field_row_frame()
        self._markdown_threads_spin = gui_element_input_spin(
            md_row,
            textvariable=self._markdown_threads_var,
            from_=MARKDOWN_THREADS_MIN,
            to=MARKDOWN_THREADS_MAX,
            width=6,
        )
        block.finish_field_row(
            md_row,
            gui_element_input_label(
                md_row, ui.markdown_threads_label, wraplength=cfg["column_label_px"]
            ),
            self._markdown_threads_spin,
        )
        block.add_comment(
            gui_element_input_description(
                block.form,
                ui.markdown_threads_hint,
                wraplength=cfg["container_width_px"],
            )
        )

        tag_row = block.add_field_row_frame()
        self._tagging_threads_spin = gui_element_input_spin(
            tag_row,
            textvariable=self._tagging_threads_var,
            from_=TAGGING_THREADS_MIN,
            to=TAGGING_THREADS_MAX,
            width=6,
        )
        block.finish_field_row(
            tag_row,
            gui_element_input_label(
                tag_row, ui.tagging_threads_label, wraplength=cfg["column_label_px"]
            ),
            self._tagging_threads_spin,
        )
        block.add_comment(
            gui_element_input_description(
                block.form,
                ui.tagging_threads_hint,
                wraplength=cfg["container_width_px"],
            )
        )

        self._pipeline_image_processing_banner = gui_element_warning_banner(
            block.form,
            ui.yandex_ocr_banner_text,
        )
        block.add_section_banner(self._pipeline_image_processing_banner)

    def _parse_int_spin(self, raw: str, low: int, high: int, default: int) -> int:
        try:
            v = int(str(raw or "").strip())
            return max(low, min(high, v))
        except (ValueError, TypeError):
            return default

    def load_pipeline(self, data: dict[str, Any] | None) -> None:
        """Заполняет виджеты из секции pipeline."""
        data = data or PipelineConfig.get_default()
        default = PipelineConfig.get_default()
        if getattr(self, "_create_documents_index_var", None):
            self._create_documents_index_var.set(
                self._bool_to_display(
                    TaggingConfig.coerce_bool(
                        data.get(KEY_CREATE_DOCUMENTS_INDEX),
                        default[KEY_CREATE_DOCUMENTS_INDEX],
                    )
                )
            )
        if getattr(self, "_extract_threads_var", None):
            self._extract_threads_var.set(str(data.get(KEY_EXTRACT_THREADS, default[KEY_EXTRACT_THREADS])))
        if getattr(self, "_image_processing_threads_var", None):
            self._image_processing_threads_var.set(
                str(data.get(KEY_IMAGE_PROCESSING_THREADS, default[KEY_IMAGE_PROCESSING_THREADS]))
            )
        if getattr(self, "_markdown_threads_var", None):
            self._markdown_threads_var.set(
                str(data.get(KEY_MARKDOWN_THREADS, default[KEY_MARKDOWN_THREADS]))
            )
        if getattr(self, "_tagging_threads_var", None):
            self._tagging_threads_var.set(
                str(data.get(KEY_TAGGING_THREADS, default[KEY_TAGGING_THREADS]))
            )

    def get_pipeline_data(self) -> dict[str, Any]:
        """Собирает данные секции pipeline из виджетов."""
        default = PipelineConfig.get_default()
        extract_th = self._parse_int_spin(
            self._extract_threads_var.get(),
            EXTRACT_THREADS_MIN,
            EXTRACT_THREADS_MAX,
            default[KEY_EXTRACT_THREADS],
        )
        ip_th = self._parse_int_spin(
            self._image_processing_threads_var.get(),
            IMAGE_PROCESSING_THREADS_MIN,
            IMAGE_PROCESSING_THREADS_MAX,
            default[KEY_IMAGE_PROCESSING_THREADS],
        )
        md_th = self._parse_int_spin(
            self._markdown_threads_var.get(),
            MARKDOWN_THREADS_MIN,
            MARKDOWN_THREADS_MAX,
            default[KEY_MARKDOWN_THREADS],
        )
        tag_th = self._parse_int_spin(
            self._tagging_threads_var.get(),
            TAGGING_THREADS_MIN,
            TAGGING_THREADS_MAX,
            default[KEY_TAGGING_THREADS],
        )
        return {
            KEY_DISCOVERY_THREADS: 1,
            KEY_CREATE_DOCUMENTS_INDEX: self._display_to_bool(
                self._create_documents_index_var.get(),
                CREATE_DOCUMENTS_INDEX_DEFAULT,
            ),
            KEY_EXTRACT_THREADS: extract_th,
            KEY_IMAGE_PROCESSING_THREADS: ip_th,
            KEY_MARKDOWN_THREADS: md_th,
            KEY_TAGGING_THREADS: tag_th,
        }
