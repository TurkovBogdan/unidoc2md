"""Экран выполнения проекта: консоль «Обработка данных» и управление запуском."""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.modules.llm_models_registry import LLMModelManager
from src.modules.project.sections.tagging_config import TAGGING_PAYLOAD_LOGIC
from src.gui.template.elements import (
    gui_element_button_primary,
    gui_element_button_secondary,
    gui_element_page_title,
)
from src.gui.utils import load_scaled_photoimage, open_folder, resolve_icon_asset_path
from src.gui.template.components import ScaledImageSlot
from src.modules.project.project_paths import ProjectPaths
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.template.styles import (
    FONT_FAMILY_UI,
    GUI_CONTENT_WRAPPER,
    GUI_TOPBAR,
    PALETTE,
    SPACING,
    UI_FONT_SIZE,
)


class ProjectPipelineScreen(BaseGUIScreen):
    """
    Экран с видимой консолью pipeline.
    Показывается при запуске проекта; консоль отображается в layout под этим экраном.
    """

    SCREEN_CODE = "project_pipeline"
    SCREEN_TITLE = "unidoc2md | Выполнение"
    # Длинная сторона иконки этапа в пикселях растра (без умножения на tk scaling).
    STAGE_ICON_MAX_SIZE = 48
    STAGE_GRID_COLUMNS = 3
    STAGE_CARD_HEIGHT_PX = 150
    # Этапы, чьё состояние в UI не берём из текста лога (модель / progress_sink).
    _STAGES_SKIP_LOG_UI = frozenset(
        {"discovery", "extract", "image_processing", "markdown", "tagging"}
    )
    _BTN_STOP_IDLE = "Остановить"
    _BTN_STOP_PENDING = "Остановка..."

    def __init__(
        self,
        parent: ttk.Frame,
        on_back,
        *,
        project_console=None,
        pipeline_storage=None,
        app_layout=None,
        on_run_request=None,
        on_stop_request=None,
        **kwargs,
    ) -> None:
        super().__init__(parent, app_layout=app_layout, **kwargs)
        self.on_back = on_back
        self._project_console = project_console
        self._pipeline_storage = pipeline_storage
        self.on_run_request = on_run_request
        self.on_stop_request = on_stop_request
        self._project_root: Path | None = None
        self._btn_back: ttk.Button | None = None
        self._btn_run: ttk.Button | None = None
        self._btn_stop: ttk.Button | None = None
        self._top_bar: tk.Frame | None = None
        self._left_frame: tk.Frame | None = None
        self._right_frame: tk.Frame | None = None
        self._stage_widgets: dict[str, dict[str, tk.Label]] = {}
        self._stage_icons: dict[str, tk.PhotoImage] = {}
        # Ссылки на Label с image= (дополнительно к PhotoImage в _stage_icons).
        self._stage_icon_labels: list[tk.Label] = []
        self._active_stage_id: str | None = None
        # Запрошена отмена: кнопка «Остановка…» disabled до on_run_done / release.
        self._cancellation_requested = False
        self._build_ui()
        self.bind("<Map>", self._on_screen_map)

    def _build_ui(self) -> None:
        self._top_panel()

        ph, pv = GUI_CONTENT_WRAPPER["padding"]
        content_wrap = tk.Frame(self, bg=GUI_CONTENT_WRAPPER["background"])
        content_wrap.pack(fill=tk.BOTH, expand=True, padx=(ph, ph), pady=(0, pv))

        self._title_label = gui_element_page_title(content_wrap, "Выполнение проекта")
        self._build_stage_panels(content_wrap)

    def _build_stage_panels(self, parent: tk.Frame) -> None:
        wrap_bg = GUI_CONTENT_WRAPPER["background"]
        panel_wrap = tk.Frame(parent, bg=wrap_bg)
        # Отступ под заголовком только из gui_element_page_title (pady_after), как на project_config / models.
        panel_wrap.pack(fill=tk.BOTH, expand=True)
        stages = [
            ("discovery", "Поиск файлов"),
            ("extract", "Извлечение содержимого"),
            ("image_processing", "Обработка изображений"),
            ("markdown", "Создание разметки"),
            ("tagging", "Теггирование и обработка"),
            ("result", "Результат"),
        ]
        cols = self.STAGE_GRID_COLUMNS
        n = len(stages)
        rows = (n + cols - 1) // cols

        card_bg = GUI_TOPBAR["background"]
        border_c = PALETTE["border"]
        fg_title = PALETTE["text_primary"]
        fg_body = PALETTE["text_soft"]
        fg_details = PALETTE["text_muted"]
        font_title = (FONT_FAMILY_UI, UI_FONT_SIZE["small"], "bold")
        font_row = (FONT_FAMILY_UI, UI_FONT_SIZE["extra_small"])
        gap = SPACING["sm"]
        pad_card = GUI_TOPBAR["padding"][0]

        # Кнопки папок проекта — над сеткой этапов (без обводки-панели).
        btn_row = tk.Frame(panel_wrap, bg=wrap_bg)
        btn_row.pack(fill=tk.X, pady=(0, gap))
        gui_element_button_secondary(
            btn_row, "Открыть документы", self._on_open_project_docs
        ).pack(side=tk.LEFT, padx=(0, SPACING["sm"]))
        gui_element_button_secondary(
            btn_row, "Открыть результаты", self._on_open_project_result
        ).pack(side=tk.LEFT)

        stages_grid = tk.Frame(panel_wrap, bg=wrap_bg)
        stages_grid.pack(fill=tk.X)
        for c in range(cols):
            stages_grid.grid_columnconfigure(c, weight=1, uniform="stage_card")
        for r in range(rows):
            # Фиксированная высота ряда под плашки; лишнее место остаётся под сеткой.
            stages_grid.grid_rowconfigure(r, weight=0)

        self._load_stage_icons()

        for idx, (stage_id, title) in enumerate(stages):
            row, col = idx // cols, idx % cols
            card = tk.Frame(
                stages_grid,
                bg=card_bg,
                highlightthickness=1,
                highlightbackground=border_c,
                highlightcolor=border_c,
                padx=pad_card,
                pady=gap,
                height=self.STAGE_CARD_HEIGHT_PX,
            )
            card.grid(
                row=row,
                column=col,
                sticky="ew",
                padx=(0, gap) if col < cols - 1 else (0, 0),
                pady=(0, gap) if row < rows - 1 else (0, 0),
            )
            card.pack_propagate(False)

            title_label = tk.Label(
                card,
                text=title,
                anchor="w",
                bg=card_bg,
                fg=fg_title,
                font=font_title,
            )
            title_label.pack(fill=tk.X, anchor="w")

            body = tk.Frame(card, bg=card_bg)
            body.pack(fill=tk.BOTH, expand=True, pady=(gap, 0))

            icon_slot = ScaledImageSlot(
                body,
                tk_scaling_ref=self,
                logical_max_pt=self.STAGE_ICON_MAX_SIZE,
                gutter=gap,
                bg=card_bg,
                scale_with_display_density=False,
            )
            # anchor=nw: при side=LEFT иначе слот центрируется по вертикали в растянутом body
            icon_slot.pack(side=tk.LEFT, padx=(0, gap), anchor=tk.NW)
            icon_slot.set_photoimage(self._stage_icons.get(stage_id))

            info_col = tk.Frame(body, bg=card_bg)
            info_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.NW)

            status_label = tk.Label(
                info_col,
                text="Статус: ожидание",
                anchor="w",
                bg=card_bg,
                fg=fg_body,
                font=font_row,
            )
            status_label.pack(fill=tk.X, pady=(0, 2))
            progress_initial = (
                "-"
                if stage_id in ("discovery", "extract", "image_processing")
                else "Прогресс: -"
            )
            progress_label = tk.Label(
                info_col,
                text=progress_initial,
                anchor="w",
                bg=card_bg,
                fg=fg_body,
                font=font_row,
            )
            progress_label.pack(fill=tk.X, pady=(0, 2))

            widgets: dict = {
                "status": status_label,
                "progress": progress_label,
            }
            if stage_id == "extract":
                content_stats_lbl = tk.Label(
                    info_col,
                    text="",
                    anchor="nw",
                    justify=tk.LEFT,
                    bg=card_bg,
                    fg=fg_details,
                    font=font_row,
                    wraplength=0,
                )
                content_stats_lbl.pack(fill=tk.BOTH, expand=True, anchor="nw")
                widgets["content_stats"] = content_stats_lbl
            elif stage_id == "image_processing":
                ip_stats_lbl = tk.Label(
                    info_col,
                    text="",
                    anchor="nw",
                    justify=tk.LEFT,
                    bg=card_bg,
                    fg=fg_details,
                    font=font_row,
                    wraplength=0,
                )
                ip_stats_lbl.pack(fill=tk.BOTH, expand=True, anchor="nw")
                widgets["image_processing_stats"] = ip_stats_lbl
            elif stage_id == "markdown":
                md_stats_lbl = tk.Label(
                    info_col,
                    text="",
                    anchor="nw",
                    justify=tk.LEFT,
                    bg=card_bg,
                    fg=fg_details,
                    font=font_row,
                    wraplength=0,
                )
                md_stats_lbl.pack(fill=tk.BOTH, expand=True, anchor="nw")
                widgets["markdown_stats"] = md_stats_lbl
            elif stage_id == "tagging":
                tag_stats_lbl = tk.Label(
                    info_col,
                    text="",
                    anchor="nw",
                    justify=tk.LEFT,
                    bg=card_bg,
                    fg=fg_details,
                    font=font_row,
                    wraplength=0,
                )
                tag_stats_lbl.pack(fill=tk.BOTH, expand=True, anchor="nw")
                widgets["tagging_stats"] = tag_stats_lbl
            elif stage_id != "discovery":
                details_label = tk.Label(
                    info_col,
                    text="Детали: -",
                    anchor="nw",
                    justify=tk.LEFT,
                    bg=card_bg,
                    fg=fg_details,
                    font=font_row,
                    wraplength=0,
                )
                details_label.pack(fill=tk.BOTH, expand=True, anchor="nw")
                widgets["details"] = details_label
            self._stage_widgets[stage_id] = widgets

    def _on_open_project_docs(self) -> None:
        self._open_project_subdir(
            lambda paths: paths.docs,
            "Папка «docs» не найдена. Добавьте каталог docs в корень проекта.",
        )

    def _on_open_project_result(self) -> None:
        self._open_project_subdir(
            lambda paths: paths.result,
            "Папка «result» не найдена. Она появится после этапа сохранения результатов.",
        )

    def _open_project_subdir(self, pick_dir, not_found_message: str) -> None:
        if self._project_root is None:
            self._show_folder_hint("Проект не выбран.")
            return
        paths = ProjectPaths.from_root(self._project_root)
        target = pick_dir(paths)
        if not target.is_dir():
            self._show_folder_hint(not_found_message)
            return
        open_folder(target)

    def _show_folder_hint(self, message: str) -> None:
        if self._app_layout is not None and self._app_layout.modals:
            self._app_layout.modals.show_info("Папка", message)

    def _load_stage_icons(self) -> None:
        icon_file_by_stage = {
            "discovery": "state-1.png",
            "extract": "state-2.png",
            "image_processing": "state-3.png",
            "markdown": "state-4.png",
            "tagging": "state-5.png",
            "result": "state-6.png",
        }
        for stage_id, file_name in icon_file_by_stage.items():
            path = resolve_icon_asset_path(file_name)
            if path is None:
                continue
            photo = load_scaled_photoimage(
                path,
                self,
                self.STAGE_ICON_MAX_SIZE,
                scale_with_display_density=False,
            )
            if photo is not None:
                self._stage_icons[stage_id] = photo

    def _top_panel(self) -> None:
        """Верхняя панель: при запуске — только Остановить; при остановке — Вернуться и Запустить проект."""
        ph, pv = GUI_TOPBAR["padding"]
        gh, _gv = GUI_TOPBAR["gap"]
        bg = GUI_TOPBAR["background"]
        self._top_bar = tk.Frame(self, bg=bg)
        self._top_bar.pack(fill=tk.X, pady=(0, pv))
        self._left_frame = tk.Frame(self._top_bar, bg=bg)
        self._left_frame.pack(side=tk.LEFT, padx=(ph, 0), pady=pv)
        self._right_frame = tk.Frame(self._top_bar, bg=bg)
        self._right_frame.pack(side=tk.RIGHT, padx=(0, ph), pady=pv)
        self._btn_back = gui_element_button_secondary(
            self._left_frame, "Вернуться", self._go_back
        )
        self._btn_run = gui_element_button_primary(
            self._right_frame, "Запустить проект", self._on_run_click
        )
        if self._pipeline_storage is not None:
            self._btn_stop = gui_element_button_primary(
                self._right_frame, self._BTN_STOP_IDLE, self._on_stop_click
            )
        self.update_buttons()

    def update_buttons(self, force_running: bool = False) -> None:
        """Показывает только Остановить при запуске, Вернуться и Запустить — при остановке."""
        if force_running:
            self._cancellation_requested = False
        running = force_running or (
            self._pipeline_storage is not None
            and self._pipeline_storage.get_current() is not None
        )
        if not running:
            self._cancellation_requested = False
        if self._btn_back is not None:
            if running:
                self._btn_back.pack_forget()
            else:
                self._btn_back.pack(side=tk.LEFT, padx=(0, GUI_TOPBAR["gap"][0]))
        if self._btn_run is not None:
            if running:
                self._btn_run.pack_forget()
            else:
                self._btn_run.pack(side=tk.LEFT)
        if self._btn_stop is not None:
            if running:
                self._btn_stop.pack(side=tk.LEFT)
                if self._cancellation_requested:
                    self._btn_stop.config(
                        state=tk.DISABLED,
                        text=self._BTN_STOP_PENDING,
                    )
                else:
                    self._btn_stop.config(
                        state=tk.NORMAL,
                        text=self._BTN_STOP_IDLE,
                    )
            else:
                self._btn_stop.pack_forget()
                self._btn_stop.config(state=tk.NORMAL, text=self._BTN_STOP_IDLE)

    def _on_screen_map(self, _event: tk.Event | None = None) -> None:
        """При показе экрана обновляем кнопки по состоянию бекенда."""
        self.update_buttons()

    def set_project_root(self, project_root: Path | None) -> None:
        """Устанавливает текущий проект (заголовок). Запуск выполняет контроллер."""
        self._project_root = project_root
        self._update_title()

    def get_project_root(self) -> Path | None:
        return self._project_root

    def _update_title(self) -> None:
        if self._project_root is not None and hasattr(self, "_title_label") and self._title_label:
            self._title_label.config(text=f"Выполнение: {self._project_root.name}")

    def show_stop_pending(self) -> None:
        """После клика «Остановить»: блокируем кнопку и показываем ожидание завершения."""
        self._cancellation_requested = True
        if self._btn_stop is not None and self._btn_stop.winfo_ismapped():
            self._btn_stop.config(
                state=tk.DISABLED,
                text=self._BTN_STOP_PENDING,
            )

    def on_run_done(self, success: bool, message: str | None = None) -> None:
        """Вызывается контроллером по завершении pipeline; обновляет кнопки и показывает результат."""
        self.update_buttons()
        if success:
            if self._active_stage_id is not None:
                self._set_stage_status(self._active_stage_id, "завершено")
        else:
            if self._active_stage_id is not None:
                self._set_stage_status(self._active_stage_id, "ошибка")
        if not success and self._app_layout:
            self._app_layout.modals.show_info("Запуск", message or "Запуск не выполнен.")

    def reset_stage_panels(self) -> None:
        self._active_stage_id = None
        for stage_id in self._stage_widgets:
            self._set_stage_status(stage_id, "ожидание")
            self._set_stage_progress(stage_id, "-")
            if stage_id == "extract":
                self._clear_extract_content_stats()
            elif stage_id == "image_processing":
                self._clear_image_processing_stats()
            elif stage_id == "markdown":
                self._clear_markdown_stats()
            elif stage_id == "tagging":
                self._clear_tagging_stats()
            else:
                self._set_stage_details(stage_id, "-")

    def set_discovery_found_count(self, count: int) -> None:
        """Явное обновление панели этапа discovery по данным этапа (не из лога)."""
        self._set_stage_status("discovery", "завершено")
        self._set_stage_progress("discovery", f"{count} файлов")

    def set_extract_documents_progress(self, done: int, total: int) -> None:
        """Прогресс извлечения из progress_sink / StageResult (не из парсинга лога)."""
        if total <= 0:
            self._set_stage_status("extract", "завершено")
        elif done >= total:
            self._set_stage_status("extract", "завершено")
        else:
            self._set_stage_status("extract", "выполняется")
        self._set_stage_progress("extract", f"{done}/{total}")

    def set_extract_content_stats(
        self,
        fragments: int | None,
        images: int | None,
    ) -> None:
        """Сводка контента после этапа extract; строки только при известных значениях."""
        widget = self._stage_widgets.get("extract", {}).get("content_stats")
        if widget is None:
            return
        parts: list[str] = []
        if fragments is not None:
            parts.append(f"Всего фрагментов: {fragments}")
        if images is not None:
            parts.append(f"Изображений: {images}")
        widget.config(text="\n".join(parts))

    def _clear_extract_content_stats(self) -> None:
        widget = self._stage_widgets.get("extract", {}).get("content_stats")
        if widget is not None:
            widget.config(text="")

    @staticmethod
    def _image_processing_stats_text(vision: dict) -> str:
        """Vision / LLM (markdown): API/кеш, токены, стоимость. OCR: API/кеш без стоимости."""
        if vision.get("billing") == "ocr":
            api_calls = int(vision.get("api_calls") or 0)
            cache_hits = int(vision.get("cache_hits") or 0)
            return "\n".join(
                [
                    f"Запросов к API: {api_calls} ({cache_hits} кеш)",
                    "Расход токенов: 0 / 0",
                ]
            )

        return ProjectPipelineScreen._llm_token_usage_stats_text(vision)

    @staticmethod
    def _llm_token_usage_stats_text(usage: dict) -> str:
        """Сводка по токенам и USD: vision (billing=vision), markdown/tagging LLM (billing=llm)."""
        p = int(usage.get("tokens_prompt") or 0)
        r = int(usage.get("tokens_reasoning") or 0)
        c = int(usage.get("tokens_completion") or 0)
        tot = int(usage.get("tokens_total") or 0)
        if tot <= p:
            tot = p + r + c
        out_tokens = max(0, tot - p)
        cache_hits = int(usage.get("cache_hits") or 0)
        api_calls = int(usage.get("api_calls") or 0)
        pi_f = LLMModelManager.optional_price_per_million(
            usage.get("price_input_per_million")
        )
        po_f = LLMModelManager.optional_price_per_million(
            usage.get("price_output_per_million")
        )

        cost_in, cost_out = LLMModelManager.costs_from_price_per_million_tokens(
            pi_f,
            po_f,
            prompt_tokens=p,
            total_tokens=tot,
        )

        parts: list[str] = [
            f"Запросов к API: {api_calls} ({cache_hits} кеш)",
            f"Расход токенов: {p} / {out_tokens}",
        ]

        if cost_in is not None and cost_out is not None:
            total_usd = cost_in + cost_out
            parts.append(f"Стоимость: ~${total_usd:.3f}")
        elif cost_in is not None:
            parts.append(f"Стоимость: ~${cost_in:.3f}")
        elif cost_out is not None:
            parts.append(f"Стоимость: ~${cost_out:.3f}")
        else:
            if api_calls == 0 and cache_hits > 0:
                parts.append("Стоимость: ~$0")
            elif api_calls > 0:
                parts.append("Стоимость: —")
            else:
                parts.append("Стоимость: ~$0")

        return "\n".join(parts)

    def set_image_processing_live_progress(self, data: dict) -> None:
        """Прогресс этапа из progress_sink: изображения + текущий расход (vision)."""
        if not isinstance(data, dict):
            return
        self._active_stage_id = "image_processing"
        done = data.get("images_done")
        total = data.get("images_total")
        if isinstance(done, int) and isinstance(total, int) and total > 0:
            # Не затирать терминальное состояние после отмены (sink может прийти позже лога).
            st = self._get_stage_status("image_processing")
            if st not in ("остановлено", "завершено", "ошибка"):
                self._set_stage_status("image_processing", "выполняется")
            self._set_stage_progress("image_processing", f"{done}/{total}")
        vision = data.get("vision")
        widget = self._stage_widgets.get("image_processing", {}).get(
            "image_processing_stats"
        )
        if widget is None:
            return
        if isinstance(vision, dict):
            widget.config(text=self._image_processing_stats_text(vision))
        else:
            widget.config(text="")

    def set_image_processing_summary(self, summary: dict) -> None:
        """Сводка этапа обработки изображений (токены, кеш/API, стоимость)."""
        self._set_stage_status("image_processing", "завершено")
        widget = self._stage_widgets.get("image_processing", {}).get(
            "image_processing_stats"
        )
        if widget is None:
            return
        vision = summary.get("vision") if isinstance(summary, dict) else None
        if not isinstance(vision, dict):
            widget.config(text="")
            return
        widget.config(text=self._image_processing_stats_text(vision))

    def _clear_image_processing_stats(self) -> None:
        widget = self._stage_widgets.get("image_processing", {}).get(
            "image_processing_stats"
        )
        if widget is not None:
            widget.config(text="")

    def _apply_llm_stage_live_snapshot(
        self, stage_id: str, stats_widget_key: str, data: dict
    ) -> None:
        """Обновление плашки этапа с LLM по данным progress_sink (как markdown, так и tagging)."""
        if not isinstance(data, dict):
            return
        self._active_stage_id = stage_id
        done = data.get("documents_done")
        total = data.get("documents_total")
        if isinstance(done, int) and isinstance(total, int) and total > 0:
            st = self._get_stage_status(stage_id)
            if st not in ("остановлено", "завершено", "ошибка"):
                self._set_stage_status(stage_id, "выполняется")
            self._set_stage_progress(stage_id, f"{done}/{total}")
        llm = data.get("llm")
        widget = self._stage_widgets.get(stage_id, {}).get(stats_widget_key)
        if widget is None:
            return
        if stage_id == "tagging":
            logic = data.get("logic")
            if logic == TAGGING_PAYLOAD_LOGIC.skip:
                widget.config(text="Режим «Пропустить»: LLM не вызывается.")
                return
            if logic == TAGGING_PAYLOAD_LOGIC.no_llm:
                widget.config(
                    text="Теги не созданы: задайте провайдер и модель в настройках проекта."
                )
                return
            if logic == TAGGING_PAYLOAD_LOGIC.create_tags_field_off:
                widget.config(
                    text="«Теггировать документы» выключено: LLM не вызывается."
                )
                return
        if isinstance(llm, dict):
            widget.config(text=self._llm_token_usage_stats_text(llm))
        else:
            widget.config(text="")

    def _apply_llm_stage_summary(
        self, stage_id: str, stats_widget_key: str, summary: dict
    ) -> None:
        """Финальная сводка LLM-этапа после StageResult (markdown / tagging)."""
        self._set_stage_status(stage_id, "завершено")
        widget = self._stage_widgets.get(stage_id, {}).get(stats_widget_key)
        if widget is None:
            return
        if stage_id == "tagging":
            logic = summary.get("logic") if isinstance(summary, dict) else None
            if logic == TAGGING_PAYLOAD_LOGIC.skip:
                widget.config(text="Режим «Пропустить»: LLM не вызывается.")
                return
            if logic == TAGGING_PAYLOAD_LOGIC.no_llm:
                widget.config(
                    text="Теги не созданы: задайте провайдер и модель в настройках проекта."
                )
                return
            if logic == TAGGING_PAYLOAD_LOGIC.create_tags_field_off:
                widget.config(
                    text="«Теггировать документы» выключено: LLM не вызывается."
                )
                return
        llm = summary.get("llm") if isinstance(summary, dict) else None
        if not isinstance(llm, dict):
            widget.config(text="")
            return
        widget.config(text=self._llm_token_usage_stats_text(llm))

    def _clear_llm_stage_stats(self, stage_id: str, stats_widget_key: str) -> None:
        widget = self._stage_widgets.get(stage_id, {}).get(stats_widget_key)
        if widget is not None:
            widget.config(text="")

    def set_markdown_live_progress(self, data: dict) -> None:
        """Прогресс markdown из progress_sink: документы + расход LLM."""
        self._apply_llm_stage_live_snapshot("markdown", "markdown_stats", data)

    def set_markdown_summary(self, summary: dict) -> None:
        """Сводка этапа markdown (токены, кеш/API, стоимость)."""
        self._apply_llm_stage_summary("markdown", "markdown_stats", summary)

    def _clear_markdown_stats(self) -> None:
        self._clear_llm_stage_stats("markdown", "markdown_stats")

    def set_tagging_live_progress(self, data: dict) -> None:
        """Прогресс tagging из progress_sink: документы + расход LLM."""
        self._apply_llm_stage_live_snapshot("tagging", "tagging_stats", data)

    def set_tagging_summary(self, summary: dict) -> None:
        """Сводка этапа tagging (токены, кеш/API, стоимость)."""
        self._apply_llm_stage_summary("tagging", "tagging_stats", summary)

    def _clear_tagging_stats(self) -> None:
        self._clear_llm_stage_stats("tagging", "tagging_stats")

    def handle_pipeline_log(self, text: str) -> None:
        raw = (text or "").strip()
        if not raw:
            return
        line = re.sub(r"^\[[A-Z]+\]\s*", "", raw).strip()
        stage_id = self._detect_stage(line)
        if stage_id is None:
            return
        if stage_id in self._STAGES_SKIP_LOG_UI:
            # Прогресс discovery/extract/image_processing идёт из sink / StageResult;
            # markdown/tagging — из progress_sink (токены/стоимость). «Остановлен» и
            # часть ошибок пишутся только в лог — без этого панель залипает в «выполняется».
            low_skip = line.lower()
            if "остановлен" in low_skip:
                self._active_stage_id = stage_id
                self._set_stage_status(stage_id, "остановлено")
                self._set_stage_details(stage_id, line)
            elif "ошибка" in low_skip:
                self._active_stage_id = stage_id
                self._set_stage_status(stage_id, "ошибка")
                self._set_stage_details(stage_id, line)
            return
        if self._active_stage_id and self._active_stage_id != stage_id:
            prev = self._active_stage_id
            prev_status = self._get_stage_status(prev)
            if prev_status == "выполняется":
                self._set_stage_status(prev, "завершено")
        self._active_stage_id = stage_id
        self._set_stage_status(stage_id, "выполняется")
        self._set_stage_details(stage_id, line)
        progress = self._extract_progress(line)
        if progress is not None:
            self._set_stage_progress(stage_id, progress)
        if "остановлен" in line.lower():
            self._set_stage_status(stage_id, "остановлено")
        if "ошибка" in line.lower():
            self._set_stage_status(stage_id, "ошибка")
        if "обработано" in line.lower() or "сохранено" in line.lower():
            self._set_stage_status(stage_id, "завершено")

    def _detect_stage(self, line: str) -> str | None:
        low = line.lower()
        if low.startswith("discovery:"):
            return "discovery"
        if low.startswith("extract:"):
            return "extract"
        if low.startswith("image processing:") or low.startswith(
            "обработка изображений:"
        ):
            return "image_processing"
        if low.startswith("markdown:"):
            return "markdown"
        if low.startswith("tagging:"):
            return "tagging"
        if low.startswith("result:"):
            return "result"
        return None

    def _extract_progress(self, line: str) -> str | None:
        match = re.search(r"(\d+)\s*/\s*(\d+)", line)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None

    def _set_stage_status(self, stage_id: str, value: str) -> None:
        widget = self._stage_widgets.get(stage_id, {}).get("status")
        if widget is not None:
            widget.config(text=f"Статус: {value}")

    def _get_stage_status(self, stage_id: str) -> str:
        widget = self._stage_widgets.get(stage_id, {}).get("status")
        if widget is None:
            return ""
        text = widget.cget("text") or ""
        if ":" not in text:
            return ""
        return text.split(":", 1)[1].strip().lower()

    def _set_stage_progress(self, stage_id: str, value: str) -> None:
        widget = self._stage_widgets.get(stage_id, {}).get("progress")
        if widget is None:
            return
        if stage_id == "discovery":
            if value in ("-", ""):
                widget.config(text="-")
            else:
                widget.config(text=value)
            return
        if stage_id == "extract":
            if value in ("-", ""):
                widget.config(text="-")
                return
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value.strip())
            if m:
                widget.config(
                    text=f"{m.group(1)} из {m.group(2)} документов",
                )
                return
            widget.config(text=f"Прогресс: {value}")
            return
        if stage_id == "image_processing":
            if value in ("-", ""):
                widget.config(text="-")
                return
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value.strip())
            if m:
                widget.config(
                    text=f"{m.group(1)} из {m.group(2)} изображений",
                )
                return
            widget.config(text=f"Прогресс: {value}")
            return
        if stage_id == "markdown":
            if value in ("-", ""):
                widget.config(text="-")
                return
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value.strip())
            if m:
                widget.config(
                    text=f"{m.group(1)} из {m.group(2)} документов",
                )
                return
            widget.config(text=f"Прогресс: {value}")
            return
        if stage_id == "tagging":
            if value in ("-", ""):
                widget.config(text="-")
                return
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value.strip())
            if m:
                widget.config(
                    text=f"{m.group(1)} из {m.group(2)} документов",
                )
                return
            widget.config(text=f"Прогресс: {value}")
            return
        widget.config(text=f"Прогресс: {value}")

    def _set_stage_details(self, stage_id: str, value: str) -> None:
        widget = self._stage_widgets.get(stage_id, {}).get("details")
        if widget is not None:
            widget.config(text=f"Детали: {value}")

    def _on_run_click(self) -> None:
        if self.on_run_request:
            self.on_run_request()

    def _on_stop_click(self) -> None:
        if self.on_stop_request:
            self.on_stop_request()

    def _go_back(self) -> None:
        if self.on_back:
            self.on_back()
