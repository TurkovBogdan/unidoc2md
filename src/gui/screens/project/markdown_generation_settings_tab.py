"""Markdown tab: mode (none / llm_processing), provider, model, LLM tuning."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from src.core import locmsg
from src.modules.llm_providers.schemas.chat import LLMChatReasoningEffort
from src.modules.project.sections.markdown_config import (
    MARKDOWN_DEFAULTS,
    MARKDOWN_GUI_MODE_HEADING_MSGID,
    MARKDOWN_KEYS,
    MARKDOWN_LOGICS,
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
    gui_element_warning_banner,
)
from src.gui.template.styles import (
    FONT_FAMILY_UI,
    PALETTE,
    UI_FONT_SIZE,
    UI_RIGHT_PANEL_NOTES_TITLE_PADY,
    UI_SETTINGS_BLOCK,
    UI_TABS,
)

_REASONING_OPTIONS: list[tuple[str, str]] = [
    (LLMChatReasoningEffort.DISABLED.value, "project_markdown.reasoning.off"),
    (LLMChatReasoningEffort.LOW.value, "project_markdown.reasoning.low"),
    (LLMChatReasoningEffort.MEDIUM.value, "project_markdown.reasoning.medium"),
    (LLMChatReasoningEffort.HIGH.value, "project_markdown.reasoning.high"),
]

_MODE_DESC_KEYS: dict[str, str] = {
    MARKDOWN_LOGICS.none: "project_markdown.mode_desc.none",
    MARKDOWN_LOGICS.llm_processing: "project_markdown.mode_desc.llm_processing",
}

_REASONING_API_CODES = frozenset(
    {
        LLMChatReasoningEffort.DISABLED.value,
        LLMChatReasoningEffort.LOW.value,
        LLMChatReasoningEffort.MEDIUM.value,
        LLMChatReasoningEffort.HIGH.value,
    }
)


def _logic_display_for_code(code: str) -> str:
    for c, msgid in MARKDOWN_LOGICS.options:
        if c == code:
            return locmsg(msgid)
    return locmsg(MARKDOWN_LOGICS.options[0][1])


def _reasoning_msgid_for_code(code: str) -> str:
    for c, msgid in _REASONING_OPTIONS:
        if c == code:
            return msgid
    return _REASONING_OPTIONS[0][1]


class MarkdownGenerationSettingsTab(ttk.Frame):
    """Text-only vs LLM markup normalization; when LLM — provider, model, tuning."""

    SETTINGS_WIDTH_PX = 520
    _SEPARATOR_PADX = 12

    def __init__(self, parent: ttk.Frame, project_root: Path, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._project_root = project_root
        self._logic_var = tk.StringVar()
        self._logic_code: str = MARKDOWN_LOGICS.none
        self._reasoning_code: str = MARKDOWN_DEFAULTS.llm_reasoning
        self._llm_frame: ttk.Frame | None = None
        self._llm_frame_row: int = 0
        self._model_settings_frame: ttk.Frame | None = None
        self._model_settings_row: int = 0
        self._provider_var = tk.StringVar()
        self._model_var = tk.StringVar()
        self._reasoning_var = tk.StringVar()
        self._temperature_var = tk.StringVar()
        self._logic_description: tk.Widget | None = None
        self._logic_combo: Any = None
        self._provider_combo: Any = None
        self._model_combo: Any = None
        self._reasoning_combo: Any = None
        self._temperature_spin: Any = None
        self._system_prompt_area: Any = None
        self._hdr_mode: ttk.Label | None = None
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
        self._temperature_quote_banner: tk.Frame | None = None
        self._lbl_system: tk.Widget | None = None
        self._desc_system: tk.Widget | None = None
        self._article_title_label: ttk.Label | None = None
        self._article_text: tk.Text | None = None
        self._build_ui()

    def _sync_logic_code_from_ui(self) -> None:
        display = (self._logic_var.get() or "").strip()
        for code, msgid in MARKDOWN_LOGICS.options:
            if locmsg(msgid) == display:
                self._logic_code = code
                return

    def _sync_reasoning_from_ui(self) -> None:
        display = (self._reasoning_var.get() or "").strip()
        for code, msgid in _REASONING_OPTIONS:
            if locmsg(msgid) == display:
                self._reasoning_code = code
                return

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
        self._logic_combo = gui_element_input_select(
            mode_row,
            variable=self._logic_var,
            values=[locmsg(msgid) for _code, msgid in MARKDOWN_LOGICS.options],
            width=28,
        )
        self._hdr_mode = gui_element_header_3(
            mode_row, locmsg(MARKDOWN_GUI_MODE_HEADING_MSGID), pack=False
        )
        self._hdr_mode.configure(wraplength=cfg["column_label_px"])
        block.finish_field_row(mode_row, self._hdr_mode, self._logic_combo)
        self._logic_var.trace_add(
            "write",
            lambda *_: (self._sync_logic_code_from_ui(), self._on_logic_change()),
        )

        self._logic_description = gui_element_input_description(
            block.form,
            locmsg("project_markdown.mode_desc.none"),
            wraplength=cfg["container_width_px"],
        )
        block.add_comment(self._logic_description)

        block.add_full_width_row(gui_element_separator(block.form))
        llm_sub, self._llm_frame, self._llm_frame_row = block.begin_sub_block()
        self._llm_header = gui_element_header_3(
            self._llm_frame, locmsg("project_markdown.section.model_choice"), pack=False
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
            p_row, locmsg("project_markdown.label.provider"), wraplength=cfg["column_label_px"]
        )
        llm_sub.finish_field_row(p_row, self._lbl_provider, self._provider_combo)
        self._provider_var.trace_add("write", lambda *_: self._on_provider_change())
        self._desc_provider = gui_element_input_description(
            self._llm_frame,
            locmsg("project_markdown.hint.provider"),
            wraplength=cfg["container_width_px"],
        )
        llm_sub.add_comment(self._desc_provider)
        m_row = llm_sub.add_field_row_frame()
        self._model_combo = gui_element_input_select(
            m_row, variable=self._model_var, values=[], width=26
        )
        self._lbl_model = gui_element_input_label(
            m_row, locmsg("project_markdown.label.model"), wraplength=cfg["column_label_px"]
        )
        llm_sub.finish_field_row(m_row, self._lbl_model, self._model_combo)
        self._desc_model = gui_element_input_description(
            self._llm_frame,
            locmsg("project_markdown.hint.model"),
            wraplength=cfg["container_width_px"],
        )
        llm_sub.add_comment(self._desc_model)

        model_sub, self._model_settings_frame, self._model_settings_row = block.begin_sub_block()
        model_sub.add_full_width_row(gui_element_separator(self._model_settings_frame))
        self._tune_header = gui_element_header_3(
            self._model_settings_frame, locmsg("project_markdown.section.model_tuning"), pack=False
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
            reason_row, locmsg("project_markdown.label.reasoning"), wraplength=cfg["column_label_px"]
        )
        model_sub.finish_field_row(reason_row, self._lbl_reasoning, self._reasoning_combo)
        self._reasoning_var.trace_add("write", lambda *_: self._sync_reasoning_from_ui())
        self._desc_reasoning = gui_element_input_description(
            self._model_settings_frame,
            locmsg("project_markdown.hint.reasoning"),
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
            temp_row, locmsg("project_markdown.label.temperature"), wraplength=cfg["column_label_px"]
        )
        model_sub.finish_field_row(temp_row, self._lbl_temperature, self._temperature_spin)
        self._desc_temperature = gui_element_input_description(
            self._model_settings_frame,
            locmsg("project_markdown.hint.temperature"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_comment(self._desc_temperature)
        self._temperature_quote_banner = gui_element_warning_banner(
            self._model_settings_frame,
            locmsg("project_markdown.hint.temperature_quote"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_custom_row(
            self._temperature_quote_banner,
            pady=UI_SETTINGS_BLOCK["warning_banner_row_pady"],
        )
        self._lbl_system = gui_element_input_label(
            self._model_settings_frame,
            locmsg("project_markdown.label.system_prompt"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_label_row(self._lbl_system)
        self._desc_system = gui_element_input_description(
            self._model_settings_frame,
            locmsg("project_markdown.hint.system_prompt"),
            wraplength=cfg["container_width_px"],
        )
        model_sub.add_comment(self._desc_system)
        self._system_prompt_area = gui_element_input_text_area(self._model_settings_frame)
        self._system_prompt_area.set(MARKDOWN_DEFAULTS.llm_system_prompt or "")
        model_sub.add_full_width_row(self._system_prompt_area)
        self._reasoning_var.set(locmsg(_reasoning_msgid_for_code(MARKDOWN_DEFAULTS.llm_reasoning)))
        self._temperature_var.set(f"{getattr(MARKDOWN_DEFAULTS, 'llm_temperature', 0.0):.1f}")
        self._sync_reasoning_from_ui()

        self._on_provider_change()
        self._on_logic_change()

        sep = tk.Frame(wrap, width=1, bg=PALETTE["border"], highlightthickness=0)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))
        sep.pack_propagate(False)

        right_frame = tk.Frame(wrap, bg=PALETTE["bg_surface"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        self._article_title_label = ttk.Label(
            right_frame,
            text=locmsg("project_markdown.notes_title"),
            style="RightPanelTitle.TLabel",
        )
        self._article_title_label.grid(row=0, column=0, sticky=tk.W, pady=UI_RIGHT_PANEL_NOTES_TITLE_PADY)
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
        self._article_text.insert(tk.END, locmsg("project_markdown.article"))
        self._article_text.configure(state=tk.DISABLED)

    def _on_logic_change(self) -> None:
        self._sync_logic_code_from_ui()
        code = self._logic_code
        if self._logic_description is not None:
            key = _MODE_DESC_KEYS.get(code)
            self._logic_description.configure(text=locmsg(key) if key else "")
        show_llm = code == MARKDOWN_LOGICS.llm_processing
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
        if code == MARKDOWN_LOGICS.llm_processing:
            opts = get_chat_provider_options()
            if opts and (not self._provider_var.get() or self._provider_var.get() not in opts):
                self._provider_var.set(opts[0])
            self._on_provider_change()

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
        if self._logic_code == MARKDOWN_LOGICS.llm_processing:
            opts = get_chat_provider_options()
            if opts and (not self._provider_var.get() or self._provider_var.get() not in opts):
                self._provider_var.set(opts[0])
        self._on_provider_change()
        self._on_logic_change()

    def refresh_locale(self) -> None:
        """Refresh tab strings after language change."""
        try:
            cfg = UI_SETTINGS_BLOCK
            if self._hdr_mode is not None:
                self._hdr_mode.configure(
                    text=locmsg(MARKDOWN_GUI_MODE_HEADING_MSGID),
                    wraplength=cfg["column_label_px"],
                )
            if self._llm_header is not None:
                self._llm_header.configure(text=locmsg("project_markdown.section.model_choice"))
            if self._tune_header is not None:
                self._tune_header.configure(text=locmsg("project_markdown.section.model_tuning"))
            for lbl, key in (
                (self._lbl_provider, "project_markdown.label.provider"),
                (self._lbl_model, "project_markdown.label.model"),
                (self._lbl_reasoning, "project_markdown.label.reasoning"),
                (self._lbl_temperature, "project_markdown.label.temperature"),
            ):
                if lbl is not None:
                    lbl.configure(text=locmsg(key), wraplength=cfg["column_label_px"])
            if self._lbl_system is not None:
                self._lbl_system.configure(
                    text=locmsg("project_markdown.label.system_prompt"),
                    wraplength=cfg["container_width_px"],
                )
            for desc, key in (
                (self._desc_provider, "project_markdown.hint.provider"),
                (self._desc_model, "project_markdown.hint.model"),
                (self._desc_reasoning, "project_markdown.hint.reasoning"),
                (self._desc_temperature, "project_markdown.hint.temperature"),
                (self._desc_system, "project_markdown.hint.system_prompt"),
            ):
                if desc is not None:
                    desc.configure(text=locmsg(key), wraplength=cfg["container_width_px"])

            banner_temp = self._temperature_quote_banner
            if banner_temp is not None and banner_temp.winfo_exists():
                ch = banner_temp.winfo_children()
                if len(ch) >= 2:
                    ch[1].configure(
                        text=locmsg("project_markdown.hint.temperature_quote"),
                        wraplength=cfg["container_width_px"],
                    )

            if self._article_title_label is not None and self._article_title_label.winfo_exists():
                self._article_title_label.configure(text=locmsg("project_markdown.notes_title"))
            if self._article_text is not None:
                self._article_text.configure(state=tk.NORMAL)
                self._article_text.delete("1.0", tk.END)
                self._article_text.insert(tk.END, locmsg("project_markdown.article"))
                self._article_text.configure(state=tk.DISABLED)

            if self._logic_combo is not None:
                self._logic_combo.set_values([locmsg(msgid) for _c, msgid in MARKDOWN_LOGICS.options])
            self._logic_var.set(_logic_display_for_code(self._logic_code))
            self._sync_logic_code_from_ui()

            reason_displays = [locmsg(msgid) for _c, msgid in _REASONING_OPTIONS]
            if self._reasoning_combo is not None:
                self._reasoning_combo.set_values(reason_displays)
            self._reasoning_var.set(locmsg(_reasoning_msgid_for_code(self._reasoning_code)))
            self._sync_reasoning_from_ui()
            self._on_logic_change()
        except tk.TclError:
            pass

    def load_markdown_settings(self, data: dict | None) -> None:
        """Load widgets from markdown section data."""
        data = data or {}
        K = MARKDOWN_KEYS
        logic_code = data.get(K.markdown_logic, MARKDOWN_LOGICS.none)
        if isinstance(logic_code, str):
            logic_code = logic_code.strip().lower()
        else:
            logic_code = MARKDOWN_LOGICS.none
        if logic_code not in MARKDOWN_LOGICS.valid_codes:
            logic_code = MARKDOWN_LOGICS.none
        self._logic_code = logic_code
        self._logic_var.set(_logic_display_for_code(logic_code))
        self._sync_logic_code_from_ui()

        self._provider_var.set(data.get(K.llm_provider, "") or "")
        self._model_var.set(data.get(K.llm_model, "") or "")

        reason_code = (data.get(K.llm_reasoning) or "").strip().lower()
        if reason_code not in _REASONING_API_CODES:
            reason_code = MARKDOWN_DEFAULTS.llm_reasoning
        self._reasoning_code = reason_code
        self._reasoning_var.set(locmsg(_reasoning_msgid_for_code(reason_code)))
        self._sync_reasoning_from_ui()

        t = data.get(K.llm_temperature)
        if t is not None:
            try:
                tf = max(0.0, min(2.0, float(t)))
                self._temperature_var.set(f"{tf:.1f}")
            except (TypeError, ValueError):
                self._temperature_var.set(f"{MARKDOWN_DEFAULTS.llm_temperature:.1f}")
        else:
            self._temperature_var.set(f"{MARKDOWN_DEFAULTS.llm_temperature:.1f}")
        system_prompt = data.get(K.llm_system_prompt)
        if system_prompt is None:
            system_prompt = MARKDOWN_DEFAULTS.llm_system_prompt or ""
        elif not isinstance(system_prompt, str):
            system_prompt = ""
        self._system_prompt_area.set(system_prompt)
        self._on_provider_change()
        self._on_logic_change()
        if logic_code == MARKDOWN_LOGICS.llm_processing:
            opts = get_chat_provider_options()
            if opts and (not self._provider_var.get() or self._provider_var.get() not in opts):
                self._provider_var.set(opts[0])
            self._on_provider_change()

    def get_markdown_settings_data(self) -> dict[str, Any]:
        """Collect markdown section from widgets."""
        self._sync_logic_code_from_ui()
        self._sync_reasoning_from_ui()
        K = MARKDOWN_KEYS
        return {
            K.markdown_logic: self._logic_code,
            K.llm_provider: (self._provider_var.get() or "").strip(),
            K.llm_model: (self._model_var.get() or "").strip(),
            K.llm_reasoning: self._reasoning_code,
            K.llm_temperature: self._temperature_spin.get_float(),
            K.llm_system_prompt: (self._system_prompt_area.get() or "").strip(),
        }
