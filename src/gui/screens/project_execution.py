"""Project run screen: pipeline console and run/stop controls."""

from __future__ import annotations

import re
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.core import locmsg
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

# Progress sentinel for markdown/tagging/result cards before run and after reset (localized in _set_stage_progress).
_PROGRESS_HEADER_IDLE = "__progress_header_idle__"


class ProjectPipelineScreen(BaseGUIScreen):
    """
    Screen with the pipeline console in the layout below this frame.

    Shown while a project run is in focus; stage cards reflect sinks and log hints.
    """

    SCREEN_CODE = "project_pipeline"
    # Stage icon raster long side in pixels (no extra tk scaling factor).
    STAGE_ICON_MAX_SIZE = 48
    STAGE_GRID_COLUMNS = 3
    STAGE_CARD_HEIGHT_PX = 150
    # Stages whose primary UI state comes from sinks / StageResult, not log text.
    _STAGES_SKIP_LOG_UI = frozenset(
        {"discovery", "extract", "image_processing", "markdown", "tagging", "result"}
    )

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
        self._btn_open_docs: ttk.Button | None = None
        self._btn_open_results: ttk.Button | None = None
        self._top_bar: tk.Frame | None = None
        self._left_frame: tk.Frame | None = None
        self._right_frame: tk.Frame | None = None
        self._stage_widgets: dict[str, dict[str, tk.Label]] = {}
        self._stage_icons: dict[str, tk.PhotoImage] = {}
        # Labels that hold stage icons (in addition to PhotoImage refs in _stage_icons).
        self._stage_icon_labels: list[tk.Label] = []
        self._active_stage_id: str | None = None
        # Stop requested: stop button stays disabled until on_run_done / release.
        self._cancellation_requested = False
        self._stage_status_code: dict[str, str] = {}
        self._stage_progress_raw: dict[str, str] = {}
        self._stage_details_raw: dict[str, str] = {}
        self._stage_title_labels: dict[str, tk.Label] = {}
        self._build_ui()
        self.bind("<Map>", self._on_screen_map)

    def _build_ui(self) -> None:
        self._top_panel()

        ph, pv = GUI_CONTENT_WRAPPER["padding"]
        content_wrap = tk.Frame(self, bg=GUI_CONTENT_WRAPPER["background"])
        content_wrap.pack(fill=tk.BOTH, expand=True, padx=(ph, ph), pady=(0, pv))

        self._title_label = gui_element_page_title(
            content_wrap, locmsg("project_execution.page_title")
        )
        self._build_stage_panels(content_wrap)

    def _build_stage_panels(self, parent: tk.Frame) -> None:
        wrap_bg = GUI_CONTENT_WRAPPER["background"]
        panel_wrap = tk.Frame(parent, bg=wrap_bg)
        # Top spacing comes from gui_element_page_title (pady_after), same as project_config / models.
        panel_wrap.pack(fill=tk.BOTH, expand=True)
        stages = (
            "discovery",
            "extract",
            "image_processing",
            "markdown",
            "tagging",
            "result",
        )
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

        # Project folder shortcuts above the stage grid (no bordered panel).
        btn_row = tk.Frame(panel_wrap, bg=wrap_bg)
        btn_row.pack(fill=tk.X, pady=(0, gap))
        self._btn_open_docs = gui_element_button_secondary(
            btn_row, locmsg("gui.project.open_documents"), self._on_open_project_docs
        )
        self._btn_open_docs.pack(side=tk.LEFT, padx=(0, SPACING["sm"]))
        self._btn_open_results = gui_element_button_secondary(
            btn_row, locmsg("gui.project.open_results"), self._on_open_project_result
        )
        self._btn_open_results.pack(side=tk.LEFT)

        stages_grid = tk.Frame(panel_wrap, bg=wrap_bg)
        stages_grid.pack(fill=tk.X)
        for c in range(cols):
            stages_grid.grid_columnconfigure(c, weight=1, uniform="stage_card")
        for r in range(rows):
            # Fixed row height for cards; extra vertical space stays below the grid.
            stages_grid.grid_rowconfigure(r, weight=0)

        self._load_stage_icons()

        for idx, stage_id in enumerate(stages):
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
                text="",
                anchor="w",
                bg=card_bg,
                fg=fg_title,
                font=font_title,
            )
            title_label.pack(fill=tk.X, anchor="w")
            title_label.config(text=locmsg(f"project_execution.stage.{stage_id}"))

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
            # anchor=NW: with side=LEFT the slot would otherwise center vertically in stretched body
            icon_slot.pack(side=tk.LEFT, padx=(0, gap), anchor=tk.NW)
            icon_slot.set_photoimage(self._stage_icons.get(stage_id))

            info_col = tk.Frame(body, bg=card_bg)
            info_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.NW)

            status_label = tk.Label(
                info_col,
                text="",
                anchor="w",
                bg=card_bg,
                fg=fg_body,
                font=font_row,
            )
            status_label.pack(fill=tk.X, pady=(0, 2))
            progress_label = tk.Label(
                info_col,
                text="",
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
            elif stage_id not in ("discovery", "result"):
                details_label = tk.Label(
                    info_col,
                    text="",
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
            self._stage_title_labels[stage_id] = title_label
            self._set_stage_status(stage_id, "idle")
            prog_init = (
                "-"
                if stage_id in ("discovery", "extract", "image_processing")
                else _PROGRESS_HEADER_IDLE
            )
            self._set_stage_progress(stage_id, prog_init)

    def _on_open_project_docs(self) -> None:
        self._open_project_subdir(
            lambda paths: paths.docs,
            locmsg("project_execution.folder_hint.docs_missing"),
        )

    def _on_open_project_result(self) -> None:
        self._open_project_subdir(
            lambda paths: paths.result,
            locmsg("project_execution.folder_hint.result_missing"),
        )

    def _open_project_subdir(self, pick_dir, not_found_message: str) -> None:
        if self._project_root is None:
            self._show_folder_hint(locmsg("project_execution.folder_hint.no_project"))
            return
        paths = ProjectPaths.from_root(self._project_root)
        target = pick_dir(paths)
        if not target.is_dir():
            self._show_folder_hint(not_found_message)
            return
        open_folder(target)

    def _show_folder_hint(self, message: str) -> None:
        if self._app_layout is not None and self._app_layout.modals:
            self._app_layout.modals.show_info(
                locmsg("project_execution.folder_modal.title"), message
            )

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
        """While running: stop only. Idle: back and run."""
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
            self._left_frame, locmsg("gui.back"), self._go_back
        )
        self._btn_run = gui_element_button_primary(
            self._right_frame, locmsg("gui.project.run"), self._on_run_click
        )
        if self._pipeline_storage is not None:
            self._btn_stop = gui_element_button_primary(
                self._right_frame, locmsg("gui.project.stop"), self._on_stop_click
            )
        self.update_buttons()

    def update_buttons(self, force_running: bool = False) -> None:
        """Toggle top bar: stop while running; back + run when idle."""
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
                        text=locmsg("gui.project.stop_pending"),
                    )
                else:
                    self._btn_stop.config(
                        state=tk.NORMAL,
                        text=locmsg("gui.project.stop"),
                    )
            else:
                self._btn_stop.pack_forget()
                self._btn_stop.config(state=tk.NORMAL, text=locmsg("gui.project.stop"))

    def _on_screen_map(self, _event: tk.Event | None = None) -> None:
        """On map, sync buttons with backend run state."""
        self.update_buttons()

    def set_project_root(self, project_root: Path | None) -> None:
        """Set current project (page title); controller owns run lifecycle."""
        self._project_root = project_root
        self._update_title()

    def get_project_root(self) -> Path | None:
        return self._project_root

    def _update_title(self) -> None:
        if not hasattr(self, "_title_label") or not self._title_label:
            return
        if self._project_root is not None:
            self._title_label.config(
                text=locmsg("project_execution.title_with_project").format(
                    name=self._project_root.name
                )
            )
        else:
            self._title_label.config(text=locmsg("project_execution.page_title"))

    def show_stop_pending(self) -> None:
        """After stop click: disable button and show pending label until pipeline ends."""
        self._cancellation_requested = True
        if self._btn_stop is not None and self._btn_stop.winfo_ismapped():
            self._btn_stop.config(
                state=tk.DISABLED,
                text=locmsg("gui.project.stop_pending"),
            )

    def on_run_done(self, success: bool, message: str | None = None) -> None:
        """Controller hook when the pipeline finishes; refresh buttons and optional error modal."""
        self.update_buttons()
        if success:
            if self._active_stage_id is not None:
                self._set_stage_status(self._active_stage_id, "done")
        else:
            if self._active_stage_id is not None:
                self._set_stage_status(self._active_stage_id, "error")
        if not success and self._app_layout:
            self._app_layout.modals.show_info(
                locmsg("project_execution.run_modal.title"),
                message or locmsg("project_execution.run_modal.failed_default"),
            )

    def reset_stage_panels(self) -> None:
        self._active_stage_id = None
        for stage_id in self._stage_widgets:
            self._set_stage_status(stage_id, "idle")
            if stage_id in ("discovery", "extract", "image_processing"):
                self._set_stage_progress(stage_id, "-")
            elif stage_id in ("markdown", "tagging", "result"):
                self._set_stage_progress(stage_id, _PROGRESS_HEADER_IDLE)
            else:
                self._set_stage_progress(stage_id, "-")
            if stage_id == "extract":
                self._clear_extract_content_stats()
            elif stage_id == "image_processing":
                self._clear_image_processing_stats()
            elif stage_id == "markdown":
                self._clear_markdown_stats()
            elif stage_id == "tagging":
                self._clear_tagging_stats()
            elif stage_id != "result":
                self._set_stage_details(stage_id, "-")

    def set_discovery_found_count(self, count: int) -> None:
        """Discovery card update from stage data (not log parsing)."""
        self._set_stage_status("discovery", "done")
        self._set_stage_progress("discovery", str(count))

    def set_extract_documents_progress(self, done: int, total: int) -> None:
        """Extract progress from progress_sink / StageResult."""
        if total <= 0:
            self._set_stage_status("extract", "done")
        elif done >= total:
            self._set_stage_status("extract", "done")
        else:
            self._set_stage_status("extract", "running")
        self._set_stage_progress("extract", f"{done}/{total}")

    def set_result_documents_progress(self, done: int, total: int) -> None:
        """Result-stage document progress from progress_sink (same pattern as extract)."""
        self._active_stage_id = "result"
        if total <= 0:
            self._set_stage_status("result", "done")
        elif done >= total:
            self._set_stage_status("result", "done")
        else:
            self._set_stage_status("result", "running")
        self._set_stage_progress("result", f"{done}/{total}")

    def set_extract_content_stats(
        self,
        fragments: int | None,
        images: int | None,
    ) -> None:
        """Post-extract content summary; omit unknown fields."""
        widget = self._stage_widgets.get("extract", {}).get("content_stats")
        if widget is None:
            return
        parts: list[str] = []
        if fragments is not None:
            parts.append(
                locmsg("project_execution.extract.fragments_total").format(n=fragments)
            )
        if images is not None:
            parts.append(locmsg("project_execution.extract.images_count").format(n=images))
        widget.config(text="\n".join(parts))

    def _clear_extract_content_stats(self) -> None:
        widget = self._stage_widgets.get("extract", {}).get("content_stats")
        if widget is not None:
            widget.config(text="")

    @staticmethod
    def _image_processing_stats_text(vision: dict) -> str:
        """Vision/LLM: API/cache, tokens, cost. OCR: API/cache only."""
        if vision.get("billing") == "ocr":
            api_calls = int(vision.get("api_calls") or 0)
            cache_hits = int(vision.get("cache_hits") or 0)
            return "\n".join(
                [
                    locmsg("project_execution.stats.api_calls_line").format(
                        api_calls=api_calls, cache_hits=cache_hits
                    ),
                    locmsg("project_execution.stats.tokens_zero_line"),
                ]
            )

        return ProjectPipelineScreen._llm_token_usage_stats_text(vision)

    @staticmethod
    def _llm_token_usage_stats_text(usage: dict) -> str:
        """Token and USD summary for vision (billing=vision) and LLM stages (billing=llm)."""
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
            locmsg("project_execution.stats.api_calls_line").format(
                api_calls=api_calls, cache_hits=cache_hits
            ),
            locmsg("project_execution.stats.tokens_usage_line").format(
                prompt=p, out_tokens=out_tokens
            ),
        ]

        if cost_in is not None and cost_out is not None:
            total_usd = cost_in + cost_out
            parts.append(
                locmsg("project_execution.stats.cost_approx").format(
                    amount=f"{total_usd:.3f}"
                )
            )
        elif cost_in is not None:
            parts.append(
                locmsg("project_execution.stats.cost_approx").format(
                    amount=f"{cost_in:.3f}"
                )
            )
        elif cost_out is not None:
            parts.append(
                locmsg("project_execution.stats.cost_approx").format(
                    amount=f"{cost_out:.3f}"
                )
            )
        else:
            if api_calls == 0 and cache_hits > 0:
                parts.append(locmsg("project_execution.stats.cost_zero"))
            elif api_calls > 0:
                parts.append(locmsg("project_execution.stats.cost_dash"))
            else:
                parts.append(locmsg("project_execution.stats.cost_zero"))

        return "\n".join(parts)

    def set_image_processing_live_progress(self, data: dict) -> None:
        """Live image_processing progress from sink: counts + running vision usage."""
        if not isinstance(data, dict):
            return
        self._active_stage_id = "image_processing"
        done = data.get("images_done")
        total = data.get("images_total")
        if isinstance(done, int) and isinstance(total, int) and total > 0:
            # Do not overwrite terminal state after cancel (sink may arrive after log line).
            st = self._get_stage_status("image_processing")
            if st not in ("stopped", "done", "error"):
                self._set_stage_status("image_processing", "running")
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
        """Final image_processing summary (tokens, cache/API, cost)."""
        self._set_stage_status("image_processing", "done")
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
        """Refresh LLM stage card from progress_sink (markdown and tagging)."""
        if not isinstance(data, dict):
            return
        self._active_stage_id = stage_id
        done = data.get("documents_done")
        total = data.get("documents_total")
        if isinstance(done, int) and isinstance(total, int) and total > 0:
            st = self._get_stage_status(stage_id)
            if st not in ("stopped", "done", "error"):
                self._set_stage_status(stage_id, "running")
            self._set_stage_progress(stage_id, f"{done}/{total}")
        llm = data.get("llm")
        widget = self._stage_widgets.get(stage_id, {}).get(stats_widget_key)
        if widget is None:
            return
        if stage_id == "tagging":
            logic = data.get("logic")
            if logic == TAGGING_PAYLOAD_LOGIC.skip:
                widget.config(text=locmsg("project_execution.tagging.skip_mode"))
                return
            if logic == TAGGING_PAYLOAD_LOGIC.no_llm:
                widget.config(text=locmsg("project_execution.tagging.no_llm_config"))
                return
            if logic == TAGGING_PAYLOAD_LOGIC.create_tags_field_off:
                widget.config(text=locmsg("project_execution.tagging.create_tags_off"))
                return
        if isinstance(llm, dict):
            widget.config(text=self._llm_token_usage_stats_text(llm))
        else:
            widget.config(text="")

    def _apply_llm_stage_summary(
        self, stage_id: str, stats_widget_key: str, summary: dict
    ) -> None:
        """Final LLM-stage summary from StageResult (markdown / tagging)."""
        self._set_stage_status(stage_id, "done")
        widget = self._stage_widgets.get(stage_id, {}).get(stats_widget_key)
        if widget is None:
            return
        if stage_id == "tagging":
            logic = summary.get("logic") if isinstance(summary, dict) else None
            if logic == TAGGING_PAYLOAD_LOGIC.skip:
                widget.config(text=locmsg("project_execution.tagging.skip_mode"))
                return
            if logic == TAGGING_PAYLOAD_LOGIC.no_llm:
                widget.config(text=locmsg("project_execution.tagging.no_llm_config"))
                return
            if logic == TAGGING_PAYLOAD_LOGIC.create_tags_field_off:
                widget.config(text=locmsg("project_execution.tagging.create_tags_off"))
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
        """Markdown live progress: documents + LLM usage from sink."""
        self._apply_llm_stage_live_snapshot("markdown", "markdown_stats", data)

    def set_markdown_summary(self, summary: dict) -> None:
        """Markdown stage summary (tokens, cache/API, cost)."""
        self._apply_llm_stage_summary("markdown", "markdown_stats", summary)

    def _clear_markdown_stats(self) -> None:
        self._clear_llm_stage_stats("markdown", "markdown_stats")

    def set_tagging_live_progress(self, data: dict) -> None:
        """Tagging live progress: documents + LLM usage from sink."""
        self._apply_llm_stage_live_snapshot("tagging", "tagging_stats", data)

    def set_tagging_summary(self, summary: dict) -> None:
        """Tagging stage summary (tokens, cache/API, cost)."""
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
            # Primary progress for these stages comes from sinks; some stop/error lines
            # only appear in the pipeline log — match keywords so the card does not stay "running".
            low_skip = line.lower()
            if "stopped" in low_skip:
                self._active_stage_id = stage_id
                self._set_stage_status(stage_id, "stopped")
                self._set_stage_details(stage_id, line)
            elif "error" in low_skip:
                self._active_stage_id = stage_id
                self._set_stage_status(stage_id, "error")
                self._set_stage_details(stage_id, line)
            return
        if self._active_stage_id and self._active_stage_id != stage_id:
            prev = self._active_stage_id
            prev_status = self._get_stage_status(prev)
            if prev_status == "running":
                self._set_stage_status(prev, "done")
        self._active_stage_id = stage_id
        self._set_stage_status(stage_id, "running")
        self._set_stage_details(stage_id, line)
        progress = self._extract_progress(line)
        if progress is not None:
            self._set_stage_progress(stage_id, progress)
        low = line.lower()
        if "stopped" in low:
            self._set_stage_status(stage_id, "stopped")
        if "error" in low:
            self._set_stage_status(stage_id, "error")
        if "saved" in low or "processed" in low or "completed" in low:
            self._set_stage_status(stage_id, "done")

    def _detect_stage(self, line: str) -> str | None:
        low = line.lower()
        if low.startswith("discovery:"):
            return "discovery"
        if low.startswith("extract:"):
            return "extract"
        if low.startswith("image processing:"):
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

    def _set_stage_status(self, stage_id: str, code: str) -> None:
        self._stage_status_code[stage_id] = code
        widget = self._stage_widgets.get(stage_id, {}).get("status")
        if widget is not None:
            widget.config(text=locmsg(f"project_execution.status_line.{code}"))

    def _get_stage_status(self, stage_id: str) -> str:
        return self._stage_status_code.get(stage_id, "idle")

    def _set_stage_progress(self, stage_id: str, value: str) -> None:
        self._stage_progress_raw[stage_id] = value
        widget = self._stage_widgets.get(stage_id, {}).get("progress")
        if widget is None:
            return
        if stage_id == "discovery":
            if value in ("-", ""):
                widget.config(text="-")
            else:
                try:
                    n = int(value)
                    widget.config(
                        text=locmsg("project_execution.discovery.files_count").format(
                            count=n
                        )
                    )
                except ValueError:
                    widget.config(text=value)
            return
        if stage_id == "extract":
            if value in ("-", ""):
                widget.config(text="-")
                return
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value.strip())
            if m:
                widget.config(
                    text=locmsg("project_execution.progress.documents_pair").format(
                        done=m.group(1), total=m.group(2)
                    )
                )
                return
            widget.config(
                text=locmsg("project_execution.progress.with_value").format(value=value)
            )
            return
        if stage_id == "image_processing":
            if value in ("-", ""):
                widget.config(text="-")
                return
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value.strip())
            if m:
                widget.config(
                    text=locmsg("project_execution.progress.images_pair").format(
                        done=m.group(1), total=m.group(2)
                    )
                )
                return
            widget.config(
                text=locmsg("project_execution.progress.with_value").format(value=value)
            )
            return
        if stage_id in ("markdown", "tagging", "result"):
            if value == _PROGRESS_HEADER_IDLE:
                widget.config(text=locmsg("project_execution.progress.header_idle"))
                return
            if value in ("-", ""):
                widget.config(text=locmsg("project_execution.progress.header_idle"))
                return
            m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", value.strip())
            if m:
                widget.config(
                    text=locmsg("project_execution.progress.documents_pair").format(
                        done=m.group(1), total=m.group(2)
                    )
                )
                return
            widget.config(
                text=locmsg("project_execution.progress.with_value").format(value=value)
            )
            return
        widget.config(
            text=locmsg("project_execution.progress.with_value").format(value=value)
        )

    def _set_stage_details(self, stage_id: str, value: str) -> None:
        if stage_id == "result":
            return
        self._stage_details_raw[stage_id] = value
        widget = self._stage_widgets.get(stage_id, {}).get("details")
        if widget is None:
            return
        widget.config(
            text=locmsg("project_execution.details.with_value").format(value=value)
        )

    def get_screen_title(self) -> str:
        return locmsg("project_execution.window_title")

    def refresh_locale(self) -> None:
        """Refresh stage titles, status lines, and progress after language change."""
        try:
            if hasattr(self, "_title_label") and self._title_label is not None:
                self._update_title()
            for sid, lbl in self._stage_title_labels.items():
                if lbl.winfo_exists():
                    lbl.configure(text=locmsg(f"project_execution.stage.{sid}"))
            for sid, code in self._stage_status_code.items():
                self._set_stage_status(sid, code)
            for sid, raw in self._stage_progress_raw.items():
                self._set_stage_progress(sid, raw)
            for sid, raw in self._stage_details_raw.items():
                self._set_stage_details(sid, raw)
            if self._btn_back is not None and self._btn_back.winfo_exists():
                self._btn_back.configure(text=locmsg("gui.back"))
            if self._btn_run is not None and self._btn_run.winfo_exists():
                self._btn_run.configure(text=locmsg("gui.project.run"))
            if self._btn_open_docs is not None and self._btn_open_docs.winfo_exists():
                self._btn_open_docs.configure(text=locmsg("gui.project.open_documents"))
            if self._btn_open_results is not None and self._btn_open_results.winfo_exists():
                self._btn_open_results.configure(text=locmsg("gui.project.open_results"))
            self.update_buttons()
            self.winfo_toplevel().title(self.get_screen_title())
        except tk.TclError:
            pass

    def _on_run_click(self) -> None:
        if self.on_run_request:
            self.on_run_request()

    def _on_stop_click(self) -> None:
        if self.on_stop_request:
            self.on_stop_request()

    def _go_back(self) -> None:
        if self.on_back:
            self.on_back()
