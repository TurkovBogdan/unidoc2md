"""Tagging tab: mode; when LLM — model pick, separator, tuning and prompts (like Markdown)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from src.core import locmsg
from src.modules.llm_providers.schemas.chat import LLMChatReasoningEffort
from src.modules.project.sections.tagging_config import (
    TAGGING_DEFAULTS,
    TAGGING_KEYS,
    TAGGING_LLM_MODES,
    TAGGING_MODES,
    TAGGING_TAG_FORMAT_VALID,
    TaggingConfig,
)

from src.gui.adapters import get_chat_models_for_provider, get_chat_provider_options
from src.gui.template.components import (
    CustomScrollbar,
    ScrollableFrame,
    SettingsBlock,
    grid_sub_block,
)
from src.gui.template.elements import (
    gui_element_header_3,
    gui_element_input_description,
    gui_element_input_label,
    gui_element_input_select,
    gui_element_input_spin_float,
    gui_element_input_text_area,
    gui_element_separator,
)
from src.gui.template.styles import (
    FONT_FAMILY_UI,
    PALETTE,
    SPACING,
    UI_FONT_SIZE,
    UI_SETTINGS_BLOCK,
    UI_TABS,
)

_REASONING_OPTIONS: list[tuple[str, str]] = [
    (LLMChatReasoningEffort.DISABLED.value, "project_tagging.reasoning.off"),
    (LLMChatReasoningEffort.LOW.value, "project_tagging.reasoning.low"),
    (LLMChatReasoningEffort.MEDIUM.value, "project_tagging.reasoning.medium"),
    (LLMChatReasoningEffort.HIGH.value, "project_tagging.reasoning.high"),
]

_MODE_DESC_KEYS: dict[str, str] = {
    TAGGING_MODES.skip: "project_tagging.mode_desc.skip",
    TAGGING_MODES.create_document_tags_linear: "project_tagging.mode_desc.linear",
    TAGGING_MODES.create_document_tags_parallel: "project_tagging.mode_desc.parallel",
}

_REASONING_API_CODES = frozenset(
    {
        LLMChatReasoningEffort.DISABLED.value,
        LLMChatReasoningEffort.LOW.value,
        LLMChatReasoningEffort.MEDIUM.value,
        LLMChatReasoningEffort.HIGH.value,
    }
)

# Stored config values (must match TaggingConfig / YAML); not translated.
_TAG_FORMAT_COMBO_VALUES: tuple[str, ...] = ("Tag_name", "tag_name")


def _mode_display_for_code(code: str) -> str:
    for c, msgid in TAGGING_MODES.options:
        if c == code:
            return locmsg(msgid)
    return locmsg(TAGGING_MODES.options[0][1])


def _reasoning_msgid_for_code(code: str) -> str:
    for c, msgid in _REASONING_OPTIONS:
        if c == code:
            return msgid
    return _REASONING_OPTIONS[0][1]


class TaggingSettingsTab(ttk.Frame):
    """Tagging mode; when LLM runs — provider, model, prompts, start tag set."""

    SETTINGS_WIDTH_PX = 520
    _SEPARATOR_PADX = 12

    def __init__(self, parent: ttk.Frame, project_root: Path, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._project_root = project_root
        self._bool_ui = (locmsg("gui.yes"), locmsg("gui.no"))
        self._mode_var = tk.StringVar()
        self._mode_code: str = TAGGING_DEFAULTS.tagging_mode
        self._reasoning_code: str = TAGGING_DEFAULTS.llm_reasoning
        self._create_tags_bool: bool = TAGGING_DEFAULTS.create_tags_field
        self._create_description_bool: bool = TAGGING_DEFAULTS.create_description_field
        self._create_date_bool: bool = TAGGING_DEFAULTS.create_date_field
        self._mode_description: tk.Widget | None = None
        self._llm_frame: ttk.Frame | None = None
        self._llm_frame_row: int = 0
        self._model_settings_frame: ttk.Frame | None = None
        self._model_settings_row: int = 0
        self._provider_var = tk.StringVar()
        self._model_var = tk.StringVar()
        self._reasoning_var = tk.StringVar()
        self._temperature_var = tk.StringVar()
        self._create_tags_field_var = tk.StringVar()
        self._tag_format_var = tk.StringVar()
        self._tag_format_row_frame: ttk.Frame | None = None
        self._tag_format_hint_widget: tk.Widget | None = None
        self._create_description_field_var = tk.StringVar()
        self._create_date_field_var = tk.StringVar()
        self._mode_combo: Any = None
        self._create_tags_combo: Any = None
        self._description_combo: Any = None
        self._date_combo: Any = None
        self._tag_format_combo: Any = None
        self._provider_combo: Any = None
        self._model_combo: Any = None
        self._reasoning_combo: Any = None
        self._temperature_spin: Any = None
        self._system_prompt_area: Any = None
        self._start_tag_set_area: Any = None
        self._lbl_mode: tk.Widget | None = None
        self._lbl_create_tags: tk.Widget | None = None
        self._hint_create_tags: tk.Widget | None = None
        self._lbl_tag_format: tk.Widget | None = None
        self._lbl_description: tk.Widget | None = None
        self._hint_description: tk.Widget | None = None
        self._lbl_date: tk.Widget | None = None
        self._hint_date: tk.Widget | None = None
        self._llm_header: ttk.Label | None = None
        self._lbl_provider: tk.Widget | None = None
        self._desc_provider: tk.Widget | None = None
        self._lbl_model: tk.Widget | None = None
        self._desc_model: tk.Widget | None = None
        self._tune_header: ttk.Label | None = None
        self._lbl_reasoning: tk.Widget | None = None
        self._desc_reasoning: tk.Widget | None = None
        self._lbl_temperature: tk.Widget | None = None
        self._desc_temperature: tk.Widget | None = None
        self._lbl_extra: tk.Widget | None = None
        self._desc_extra: tk.Widget | None = None
        self._lbl_start_tags: tk.Widget | None = None
        self._desc_start_tags: tk.Widget | None = None
        self._article_title_label: ttk.Label | None = None
        self._article_text: tk.Text | None = None
        self._build_ui()

    def _tagging_bool_to_display(self, b: bool) -> str:
        return self._bool_ui[0] if b else self._bool_ui[1]

    def _tagging_display_to_bool(self, display: str, default: bool) -> bool:
        d = (display or "").strip()
        if d == self._bool_ui[0]:
            return True
        if d == self._bool_ui[1]:
            return False
        return default

    def _sync_mode_code_from_ui(self) -> None:
        display = (self._mode_var.get() or "").strip()
        for code, msgid in TAGGING_MODES.options:
            if locmsg(msgid) == display:
                self._mode_code = code
                return

    def _sync_reasoning_from_ui(self) -> None:
        display = (self._reasoning_var.get() or "").strip()
        for code, msgid in _REASONING_OPTIONS:
            if locmsg(msgid) == display:
                self._reasoning_code = code
                return

    def _sync_field_bools_from_ui(self) -> None:
        self._create_tags_bool = self._tagging_display_to_bool(
            self._create_tags_field_var.get(), TAGGING_DEFAULTS.create_tags_field
        )
        self._create_description_bool = self._tagging_display_to_bool(
            self._create_description_field_var.get(), TAGGING_DEFAULTS.create_description_field
        )
        self._create_date_bool = self._tagging_display_to_bool(
            self._create_date_field_var.get(), TAGGING_DEFAULTS.create_date_field
        )

    def _build_ui(self) -> None:
        padx, pady = UI_TABS["content_padding"]
        wrap = ttk.Frame(self)
        wrap.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)

        left_frame = tk.Frame(wrap, width=self.SETTINGS_WIDTH_PX, bg=PALETTE["bg_surface"])
        left_frame.pack_propagate(False)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))
        self._scroll = ScrollableFrame(left_frame)
        self._scroll.pack(fill=tk.BOTH, expand=True, padx=(0, self._SEPARATOR_PADX))
        cfg = UI_SETTINGS_BLOCK
        block = SettingsBlock(self._scroll.content_frame)

        mode_row = block.add_field_row_frame()
        self._mode_combo = gui_element_input_select(
            mode_row,
            variable=self._mode_var,
            values=[locmsg(msgid) for _code, msgid in TAGGING_MODES.options],
            width=28,
        )
        self._lbl_mode = gui_element_input_label(
            mode_row, locmsg("project_tagging.mode_field_label"), wraplength=cfg["column_label_px"]
        )
        block.finish_field_row(mode_row, self._lbl_mode, self._mode_combo)
        self._mode_var.trace_add(
            "write",
            lambda *_: (self._sync_mode_code_from_ui(), self._on_mode_change()),
        )

        self._mode_description = gui_element_input_description(
            block.form,
            locmsg("project_tagging.mode_desc.skip"),
            wraplength=cfg["container_width_px"],
        )
        block.add_comment(self._mode_description)

        row_ct = block.add_field_row_frame()
        self._create_tags_combo = gui_element_input_select(
            row_ct,
            variable=self._create_tags_field_var,
            values=list(self._bool_ui),
            width=28,
        )
        self._lbl_create_tags = gui_element_input_label(
            row_ct, locmsg("project_tagging.field.create_tags_label"), wraplength=cfg["column_label_px"]
        )
        block.finish_field_row(row_ct, self._lbl_create_tags, self._create_tags_combo)
        self._hint_create_tags = gui_element_input_description(
            block.form,
            locmsg("project_tagging.field.create_tags_hint"),
            wraplength=cfg["container_width_px"],
        )
        block.add_comment(self._hint_create_tags)

        self._tag_format_row_frame = block.add_field_row_frame()
        self._tag_format_combo = gui_element_input_select(
            self._tag_format_row_frame,
            variable=self._tag_format_var,
            values=list(_TAG_FORMAT_COMBO_VALUES),
            width=28,
        )
        self._lbl_tag_format = gui_element_input_label(
            self._tag_format_row_frame,
            locmsg("project_tagging.field.tag_format_label"),
            wraplength=cfg["column_label_px"],
        )
        block.finish_field_row(
            self._tag_format_row_frame, self._lbl_tag_format, self._tag_format_combo
        )
        self._tag_format_hint_widget = gui_element_input_description(
            block.form,
            locmsg("project_tagging.field.tag_format_hint"),
            wraplength=cfg["container_width_px"],
        )
        block.add_comment(self._tag_format_hint_widget)

        self._create_tags_field_var.trace_add(
            "write",
            lambda *_: (self._sync_field_bools_from_ui(), self._sync_tag_format_visibility()),
        )

        row_d = block.add_field_row_frame()
        self._description_combo = gui_element_input_select(
            row_d,
            variable=self._create_description_field_var,
            values=list(self._bool_ui),
            width=28,
        )
        self._lbl_description = gui_element_input_label(
            row_d, locmsg("project_tagging.field.description_label"), wraplength=cfg["column_label_px"]
        )
        block.finish_field_row(row_d, self._lbl_description, self._description_combo)
        self._hint_description = gui_element_input_description(
            block.form,
            locmsg("project_tagging.field.description_hint"),
            wraplength=cfg["container_width_px"],
        )
        block.add_comment(self._hint_description)

        row_dt = block.add_field_row_frame()
        self._date_combo = gui_element_input_select(
            row_dt,
            variable=self._create_date_field_var,
            values=list(self._bool_ui),
            width=28,
        )
        self._lbl_date = gui_element_input_label(
            row_dt, locmsg("project_tagging.field.date_label"), wraplength=cfg["column_label_px"]
        )
        block.finish_field_row(row_dt, self._lbl_date, self._date_combo)
        self._hint_date = gui_element_input_description(
            block.form,
            locmsg("project_tagging.field.date_hint"),
            wraplength=cfg["container_width_px"],
        )
        block.add_comment(self._hint_date)

        self._create_description_field_var.trace_add(
            "write", lambda *_: self._sync_field_bools_from_ui()
        )
        self._create_date_field_var.trace_add("write", lambda *_: self._sync_field_bools_from_ui())

        block.add_full_width_row(gui_element_separator(block.form))

        llm_sub, self._llm_frame, self._llm_frame_row = block.begin_sub_block()
        self._llm_header = gui_element_header_3(
            self._llm_frame, locmsg("project_tagging.section.model_choice"), pack=False
        )
        llm_sub.add_comment(self._llm_header)
        p_row = llm_sub.add_field_row_frame()
        self._provider_combo = gui_element_input_select(
            p_row,
            variable=self._provider_var,
            values=get_chat_provider_options(),
            width=26,
        )
        self._lbl_provider = gui_element_input_label(
            p_row, locmsg("project_tagging.label.provider"), wraplength=cfg["column_label_px"]
        )
        llm_sub.finish_field_row(p_row, self._lbl_provider, self._provider_combo)
        self._provider_var.trace_add("write", lambda *_: self._on_provider_change())
        self._desc_provider = gui_element_input_description(
            self._llm_frame,
            locmsg("project_tagging.hint.provider"),
            wraplength=cfg["container_width_px"],
        )
        llm_sub.add_comment(self._desc_provider)
        m_row = llm_sub.add_field_row_frame()
        self._model_combo = gui_element_input_select(
            m_row, variable=self._model_var, values=[], width=26
        )
        self._lbl_model = gui_element_input_label(
            m_row, locmsg("project_tagging.label.model"), wraplength=cfg["column_label_px"]
        )
        llm_sub.finish_field_row(m_row, self._lbl_model, self._model_combo)
        self._desc_model = gui_element_input_description(
            self._llm_frame,
            locmsg("project_tagging.hint.model"),
            wraplength=cfg["container_width_px"],
        )
        llm_sub.add_comment(self._desc_model)

        model_sub, self._model_settings_frame, self._model_settings_row = block.begin_sub_block()
        model_sub.add_full_width_row(gui_element_separator(self._model_settings_frame))
        self._tune_header = gui_element_header_3(
            self._model_settings_frame,
            locmsg("project_tagging.section.model_tuning"),
            pack=False,
        )
        model_sub.add_comment(self._tune_header)
        reason_row = model_sub.add_field_row_frame()
        reason_displays = [locmsg(msgid) for _code, msgid in _REASONING_OPTIONS]
        self._reasoning_combo = gui_element_input_select(
            reason_row,
            variable=self._reasoning_var,
            values=reason_displays,
            width=26,
        )
        self._lbl_reasoning = gui_element_input_label(
            reason_row, locmsg("project_tagging.label.reasoning"), wraplength=cfg["column_label_px"]
        )
        model_sub.finish_field_row(reason_row, self._lbl_reasoning, self._reasoning_combo)
        self._reasoning_var.trace_add("write", lambda *_: self._sync_reasoning_from_ui())
        self._desc_reasoning = gui_element_input_description(
            self._model_settings_frame,
            locmsg("project_tagging.hint.reasoning"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_comment(self._desc_reasoning)
        temp_row = model_sub.add_field_row_frame()
        self._temperature_spin = gui_element_input_spin_float(
            temp_row,
            textvariable=self._temperature_var,
            from_=0.0,
            to=2.0,
            increment=0.1,
            width=6,
            decimals=1,
        )
        self._lbl_temperature = gui_element_input_label(
            temp_row, locmsg("project_tagging.label.temperature"), wraplength=cfg["column_label_px"]
        )
        model_sub.finish_field_row(temp_row, self._lbl_temperature, self._temperature_spin)
        self._desc_temperature = gui_element_input_description(
            self._model_settings_frame,
            locmsg("project_tagging.hint.temperature"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_comment(self._desc_temperature)

        self._lbl_extra = gui_element_input_label(
            self._model_settings_frame,
            locmsg("project_tagging.label.extra_instructions"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_label_row(self._lbl_extra)
        self._desc_extra = gui_element_input_description(
            self._model_settings_frame,
            locmsg("project_tagging.hint.extra_instructions"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_comment(self._desc_extra)
        self._system_prompt_area = gui_element_input_text_area(self._model_settings_frame)
        self._system_prompt_area.set("")
        model_sub.add_full_width_row(self._system_prompt_area)
        _prompt_blocks_gap = tk.Frame(
            self._model_settings_frame,
            height=SPACING["md"],
            bg=PALETTE["bg_surface"],
        )
        _prompt_blocks_gap.grid_propagate(False)
        model_sub.add_full_width_row(_prompt_blocks_gap)

        self._lbl_start_tags = gui_element_input_label(
            self._model_settings_frame,
            locmsg("project_tagging.label.start_tags"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_label_row(self._lbl_start_tags)
        self._desc_start_tags = gui_element_input_description(
            self._model_settings_frame,
            locmsg("project_tagging.hint.start_tags"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_comment(self._desc_start_tags)
        self._start_tag_set_area = gui_element_input_text_area(self._model_settings_frame)
        self._start_tag_set_area.set(TAGGING_DEFAULTS.start_tag_set or "")
        model_sub.add_full_width_row(self._start_tag_set_area)

        self._reasoning_var.set(locmsg(_reasoning_msgid_for_code(TAGGING_DEFAULTS.llm_reasoning)))
        self._temperature_var.set(f"{getattr(TAGGING_DEFAULTS, 'llm_temperature', 0.3):.1f}")
        self._mode_var.set(_mode_display_for_code(TAGGING_DEFAULTS.tagging_mode))
        self._sync_mode_code_from_ui()
        self._create_tags_field_var.set(self._tagging_bool_to_display(TAGGING_DEFAULTS.create_tags_field))
        self._tag_format_var.set(TAGGING_DEFAULTS.tag_format)
        self._create_description_field_var.set(
            self._tagging_bool_to_display(TAGGING_DEFAULTS.create_description_field)
        )
        self._create_date_field_var.set(self._tagging_bool_to_display(TAGGING_DEFAULTS.create_date_field))
        self._sync_field_bools_from_ui()
        self._sync_reasoning_from_ui()

        self._on_provider_change()
        self._on_mode_change()
        self._sync_tag_format_visibility()

        sep = tk.Frame(wrap, width=1, bg=PALETTE["border"], highlightthickness=0)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))
        sep.pack_propagate(False)

        right_frame = tk.Frame(wrap, bg=PALETTE["bg_surface"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        self._article_title_label = ttk.Label(
            right_frame,
            text=locmsg("project_tagging.notes_title"),
            style="RightPanelTitle.TLabel",
        )
        self._article_title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
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
        self._article_scrollbar = CustomScrollbar(article_container, command=self._article_text.yview)
        self._article_text.configure(yscrollcommand=self._article_scrollbar.set)
        self._article_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._article_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._article_text.configure(state=tk.NORMAL)
        self._article_text.insert(tk.END, locmsg("project_tagging.article"))
        self._article_text.configure(state=tk.DISABLED)

    def _sync_tag_format_visibility(self) -> None:
        """Show tag format row only when «create tags» is enabled."""
        row = self._tag_format_row_frame
        hint = self._tag_format_hint_widget
        if row is None or hint is None:
            return
        show = self._tagging_display_to_bool(
            self._create_tags_field_var.get(), TAGGING_DEFAULTS.create_tags_field
        )
        if show:
            row.grid()
            hint.grid()
        else:
            row.grid_remove()
            hint.grid_remove()

    def _on_mode_change(self) -> None:
        self._sync_mode_code_from_ui()
        code = self._mode_code
        if self._mode_description is not None:
            key = _MODE_DESC_KEYS.get(code)
            self._mode_description.configure(text=locmsg(key) if key else "")
        show_llm = code in TAGGING_LLM_MODES
        if self._llm_frame is not None:
            if show_llm:
                grid_sub_block(self._llm_frame, self._llm_frame_row)
            else:
                self._llm_frame.grid_remove()
        if self._model_settings_frame is not None:
            if show_llm:
                grid_sub_block(self._model_settings_frame, self._model_settings_row)
            else:
                self._model_settings_frame.grid_remove()

    def _on_provider_change(self) -> None:
        provider = (self._provider_var.get() or "").strip()
        models = get_chat_models_for_provider(provider)
        self._model_combo.set_values(models)
        if models and (not self._model_var.get() or self._model_var.get() not in models):
            self._model_var.set(models[0])

    def refresh_options(self) -> None:
        """Refresh provider/model lists when the screen is shown."""
        if self._provider_combo is not None:
            self._provider_combo.set_values(get_chat_provider_options())
        self._on_provider_change()
        self._on_mode_change()
        self._sync_tag_format_visibility()

    def refresh_locale(self) -> None:
        """Refresh tab strings after language change."""
        try:
            cfg = UI_SETTINGS_BLOCK
            self._bool_ui = (locmsg("gui.yes"), locmsg("gui.no"))
            for combo, bval in (
                (self._create_tags_combo, self._create_tags_bool),
                (self._description_combo, self._create_description_bool),
                (self._date_combo, self._create_date_bool),
            ):
                if combo is not None:
                    combo.set_values(list(self._bool_ui))
            self._create_tags_field_var.set(self._tagging_bool_to_display(self._create_tags_bool))
            self._create_description_field_var.set(
                self._tagging_bool_to_display(self._create_description_bool)
            )
            self._create_date_field_var.set(self._tagging_bool_to_display(self._create_date_bool))

            if self._lbl_mode is not None:
                self._lbl_mode.configure(
                    text=locmsg("project_tagging.mode_field_label"),
                    wraplength=cfg["column_label_px"],
                )
            if self._lbl_create_tags is not None:
                self._lbl_create_tags.configure(
                    text=locmsg("project_tagging.field.create_tags_label"),
                    wraplength=cfg["column_label_px"],
                )
            if self._hint_create_tags is not None:
                self._hint_create_tags.configure(
                    text=locmsg("project_tagging.field.create_tags_hint"),
                    wraplength=cfg["container_width_px"],
                )
            if self._lbl_tag_format is not None:
                self._lbl_tag_format.configure(
                    text=locmsg("project_tagging.field.tag_format_label"),
                    wraplength=cfg["column_label_px"],
                )
            if self._tag_format_hint_widget is not None:
                self._tag_format_hint_widget.configure(
                    text=locmsg("project_tagging.field.tag_format_hint"),
                    wraplength=cfg["container_width_px"],
                )
            if self._lbl_description is not None:
                self._lbl_description.configure(
                    text=locmsg("project_tagging.field.description_label"),
                    wraplength=cfg["column_label_px"],
                )
            if self._hint_description is not None:
                self._hint_description.configure(
                    text=locmsg("project_tagging.field.description_hint"),
                    wraplength=cfg["container_width_px"],
                )
            if self._lbl_date is not None:
                self._lbl_date.configure(
                    text=locmsg("project_tagging.field.date_label"),
                    wraplength=cfg["column_label_px"],
                )
            if self._hint_date is not None:
                self._hint_date.configure(
                    text=locmsg("project_tagging.field.date_hint"),
                    wraplength=cfg["container_width_px"],
                )
            if self._llm_header is not None:
                self._llm_header.configure(text=locmsg("project_tagging.section.model_choice"))
            if self._tune_header is not None:
                self._tune_header.configure(text=locmsg("project_tagging.section.model_tuning"))
            for lbl, key in (
                (self._lbl_provider, "project_tagging.label.provider"),
                (self._lbl_model, "project_tagging.label.model"),
                (self._lbl_reasoning, "project_tagging.label.reasoning"),
                (self._lbl_temperature, "project_tagging.label.temperature"),
            ):
                if lbl is not None:
                    lbl.configure(text=locmsg(key), wraplength=cfg["column_label_px"])
            if self._lbl_extra is not None:
                self._lbl_extra.configure(
                    text=locmsg("project_tagging.label.extra_instructions"),
                    wraplength=cfg["container_width_px"],
                )
            if self._lbl_start_tags is not None:
                self._lbl_start_tags.configure(
                    text=locmsg("project_tagging.label.start_tags"),
                    wraplength=cfg["container_width_px"],
                )
            for desc, key in (
                (self._desc_provider, "project_tagging.hint.provider"),
                (self._desc_model, "project_tagging.hint.model"),
                (self._desc_reasoning, "project_tagging.hint.reasoning"),
                (self._desc_temperature, "project_tagging.hint.temperature"),
                (self._desc_extra, "project_tagging.hint.extra_instructions"),
                (self._desc_start_tags, "project_tagging.hint.start_tags"),
            ):
                if desc is not None:
                    desc.configure(text=locmsg(key), wraplength=cfg["container_width_px"])

            if self._article_title_label is not None and self._article_title_label.winfo_exists():
                self._article_title_label.configure(text=locmsg("project_tagging.notes_title"))
            if self._article_text is not None:
                self._article_text.configure(state=tk.NORMAL)
                self._article_text.delete("1.0", tk.END)
                self._article_text.insert(tk.END, locmsg("project_tagging.article"))
                self._article_text.configure(state=tk.DISABLED)

            if self._mode_combo is not None:
                self._mode_combo.set_values([locmsg(msgid) for _c, msgid in TAGGING_MODES.options])
            self._mode_var.set(_mode_display_for_code(self._mode_code))
            self._sync_mode_code_from_ui()

            if self._tag_format_combo is not None:
                self._tag_format_combo.set_values(list(_TAG_FORMAT_COMBO_VALUES))
            self._tag_format_var.set(
                TaggingConfig.coerce_tag_format(self._tag_format_var.get(), TAGGING_DEFAULTS.tag_format)
            )

            reason_displays = [locmsg(msgid) for _c, msgid in _REASONING_OPTIONS]
            if self._reasoning_combo is not None:
                self._reasoning_combo.set_values(reason_displays)
            self._reasoning_var.set(locmsg(_reasoning_msgid_for_code(self._reasoning_code)))
            self._sync_reasoning_from_ui()

            self.refresh_options()
        except tk.TclError:
            pass

    def load_tagging_settings(self, data: dict | None) -> None:
        """Load widgets from tagging section data."""
        data = data or {}
        K = TAGGING_KEYS
        mode_code = data.get(K.tagging_mode, TAGGING_DEFAULTS.tagging_mode)
        if mode_code == "create_document_tags":
            mode_code = TAGGING_MODES.create_document_tags_linear
        if isinstance(mode_code, str):
            mode_code = mode_code.strip().lower()
        else:
            mode_code = TAGGING_DEFAULTS.tagging_mode
        if mode_code not in TAGGING_MODES.valid_codes:
            mode_code = TAGGING_DEFAULTS.tagging_mode
        self._mode_code = mode_code
        self._mode_var.set(_mode_display_for_code(mode_code))
        self._sync_mode_code_from_ui()

        self._create_tags_bool = TaggingConfig.coerce_bool(
            data.get(K.create_tags_field), TAGGING_DEFAULTS.create_tags_field
        )
        self._create_tags_field_var.set(self._tagging_bool_to_display(self._create_tags_bool))

        self._tag_format_var.set(
            TaggingConfig.coerce_tag_format(data.get(K.tag_format), TAGGING_DEFAULTS.tag_format)
        )

        self._create_description_bool = TaggingConfig.coerce_bool(
            data.get(K.create_description_field), TAGGING_DEFAULTS.create_description_field
        )
        self._create_description_field_var.set(
            self._tagging_bool_to_display(self._create_description_bool)
        )

        self._create_date_bool = TaggingConfig.coerce_bool(
            data.get(K.create_date_field), TAGGING_DEFAULTS.create_date_field
        )
        self._create_date_field_var.set(self._tagging_bool_to_display(self._create_date_bool))

        self._provider_var.set(data.get(K.llm_provider, "") or "")
        self._model_var.set(data.get(K.llm_model, "") or "")

        reason_code = (data.get(K.llm_reasoning) or "").strip().lower()
        if reason_code not in _REASONING_API_CODES:
            reason_code = TAGGING_DEFAULTS.llm_reasoning
        self._reasoning_code = reason_code
        self._reasoning_var.set(locmsg(_reasoning_msgid_for_code(reason_code)))
        self._sync_reasoning_from_ui()

        t = data.get(K.llm_temperature)
        if t is not None:
            try:
                tf = max(0.0, min(2.0, float(t)))
                self._temperature_var.set(f"{tf:.1f}")
            except (TypeError, ValueError):
                self._temperature_var.set(f"{TAGGING_DEFAULTS.llm_temperature:.1f}")
        else:
            self._temperature_var.set(f"{TAGGING_DEFAULTS.llm_temperature:.1f}")
        extra = data.get(K.llm_additional_instructions)
        if extra is None or not isinstance(extra, str):
            extra = ""
        self._system_prompt_area.set(extra.strip())
        start_tag_set = data.get(K.start_tag_set)
        if start_tag_set is None:
            start_tag_set = TAGGING_DEFAULTS.start_tag_set or ""
        elif not isinstance(start_tag_set, str):
            start_tag_set = ""
        self._start_tag_set_area.set(start_tag_set)
        self._on_provider_change()
        self._on_mode_change()
        self._sync_tag_format_visibility()
        if self._mode_code in TAGGING_LLM_MODES:
            opts = get_chat_provider_options()
            if opts and (not self._provider_var.get() or self._provider_var.get() not in opts):
                self._provider_var.set(opts[0])
            self._on_provider_change()

    def get_tagging_settings_data(self) -> dict[str, Any]:
        """Collect tagging section from widgets."""
        self._sync_mode_code_from_ui()
        self._sync_reasoning_from_ui()
        self._sync_field_bools_from_ui()
        K = TAGGING_KEYS
        return {
            K.tagging_mode: self._mode_code,
            K.create_tags_field: self._create_tags_bool,
            K.tag_format: TaggingConfig.coerce_tag_format(
                self._tag_format_var.get(), TAGGING_DEFAULTS.tag_format
            ),
            K.create_description_field: self._create_description_bool,
            K.create_date_field: self._create_date_bool,
            K.llm_provider: (self._provider_var.get() or "").strip(),
            K.llm_model: (self._model_var.get() or "").strip(),
            K.llm_reasoning: self._reasoning_code,
            K.llm_temperature: self._temperature_spin.get_float(),
            K.llm_additional_instructions: (self._system_prompt_area.get() or "").strip(),
            K.start_tag_set: (self._start_tag_set_area.get() or "").strip(),
        }
