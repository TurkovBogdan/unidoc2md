"""Per-model LLM provider editor screen."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.core import locmsg
from src.gui.adapters import get_llm_models_adapter
from src.gui.template.components import CustomScrollbar
from src.gui.template.components.llm_provider_model_detail import LLMProviderModelDetail
from src.gui.template.elements import gui_element_button_primary, gui_element_button_secondary
from src.gui.template.elements.typography import gui_element_page_title
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.template.styles import (
    FONT_FAMILY_UI,
    GUI_CONTENT_WRAPPER,
    GUI_TOPBAR,
    PALETTE,
    UI_FONT_SIZE,
    UI_TABS,
)


class ModelSettingsDetailScreen(BaseGUIScreen):
    """Edit one model; layout matches project settings tabs (wider form)."""

    SCREEN_CODE = "model_settings_detail"

    # Wider than default 520px project tabs — two-column model form reads better.
    SETTINGS_WIDTH_PX = 680
    _SEPARATOR_PADX = 12
    _MODEL_CODE_HEADING_MAX = 56

    def __init__(
        self,
        parent: ttk.Frame,
        app_root: Path,
        on_back=None,
        *,
        app_layout=None,
        **kwargs,
    ) -> None:
        super().__init__(parent, app_root=app_root, app_layout=app_layout, **kwargs)
        self.app_root = Path(app_root)
        self.on_back = on_back
        self._manager = get_llm_models_adapter(self.app_root)
        self._save_btn: ttk.Button | None = None
        self._back_btn: ttk.Button | None = None
        self._title_label: tk.Widget | None = None
        self._article_label: ttk.Label | None = None
        self._article_text: tk.Text | None = None
        self._detail: LLMProviderModelDetail | None = None
        self._model_key: str | None = None
        self._build_ui()
        self.bind("<Map>", self._on_screen_show)

    @staticmethod
    def _short_model_code(code: str, *, max_len: int = _MODEL_CODE_HEADING_MAX) -> str:
        s = (code or "").strip()
        if len(s) <= max_len:
            return s
        if max_len <= 1:
            return "…"
        return s[: max_len - 1] + "…"

    def get_screen_title(self) -> str:
        if self._model_key:
            model = self._manager.get_model(self._model_key)
            if model is not None:
                code = self._short_model_code(model.code)
                return f"unidoc2md | {model.provider_code} | {code}"
        return locmsg("models.detail.window_title")

    def _update_page_heading(self) -> None:
        if self._title_label is None:
            return
        if not self._model_key:
            self._title_label.configure(text=locmsg("models.detail.page_title"))
            return
        model = self._manager.get_model(self._model_key)
        if model is None:
            self._title_label.configure(text=locmsg("models.detail.page_title"))
            return
        code = self._short_model_code(model.code)
        self._title_label.configure(text=f"{model.provider_code} | {code}")

    def refresh_locale(self) -> None:
        if self._back_btn is not None:
            self._back_btn.configure(text=locmsg("gui.back"))
        if self._save_btn is not None:
            self._save_btn.configure(text=locmsg("gui.save"))
        self._update_page_heading()
        if self._article_label is not None:
            self._article_label.configure(text=locmsg("models.detail.sidebar_title"))
        if self._article_text is not None:
            self._article_text.configure(state=tk.NORMAL)
            self._article_text.delete("1.0", tk.END)
            self._article_text.insert(tk.END, locmsg("models.detail.article"))
            self._article_text.configure(state=tk.DISABLED)
        try:
            self.winfo_toplevel().title(self.get_screen_title())
        except tk.TclError:
            pass
        if self._detail is not None:
            self._detail.refresh_locale()

    def _on_screen_show(self, event=None) -> None:
        self.refresh_locale()

    def _build_ui(self) -> None:
        self._top_panel()

        ph, pv = GUI_CONTENT_WRAPPER["padding"]
        content_wrap = tk.Frame(self, bg=GUI_CONTENT_WRAPPER["background"])
        content_wrap.pack(fill=tk.BOTH, expand=True, padx=(ph, ph), pady=(0, pv))

        self._title_label = gui_element_page_title(content_wrap, locmsg("models.detail.page_title"))
        self._title_label.configure(wraplength=self.SETTINGS_WIDTH_PX)

        tpadx, tpady = UI_TABS["content_padding"]
        wrap = ttk.Frame(content_wrap)
        wrap.pack(fill=tk.BOTH, expand=True, padx=tpadx, pady=tpady)

        left_frame = tk.Frame(wrap, width=self.SETTINGS_WIDTH_PX, bg=PALETTE["bg_surface"])
        left_frame.pack_propagate(False)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))

        self._detail = LLMProviderModelDetail(left_frame)
        self._detail.pack(fill=tk.BOTH, expand=True)
        self._detail.set_model(None)
        self._update_save_button_state()
        self._update_page_heading()

        sep = tk.Frame(wrap, width=1, bg=PALETTE["border"], highlightthickness=0)
        sep.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))
        sep.pack_propagate(False)

        right_frame = tk.Frame(wrap, bg=PALETTE["bg_surface"])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)

        self._article_label = ttk.Label(
            right_frame,
            text=locmsg("models.detail.sidebar_title"),
            style="RightPanelTitle.TLabel",
        )
        self._article_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 4))

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
        article_scroll = CustomScrollbar(article_container, command=self._article_text.yview)
        self._article_text.configure(yscrollcommand=article_scroll.set)
        article_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._article_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._article_text.configure(state=tk.NORMAL)
        self._article_text.insert(tk.END, locmsg("models.detail.article"))
        self._article_text.configure(state=tk.DISABLED)

    def _top_panel(self) -> None:
        """Top bar: back left; save right (same as project settings)."""
        ph, pv = GUI_TOPBAR["padding"]
        gh, _gv = GUI_TOPBAR["gap"]
        bg = GUI_TOPBAR["background"]
        top_bar = tk.Frame(self, bg=bg)
        top_bar.pack(fill=tk.X, pady=(0, pv))
        left_frame = tk.Frame(top_bar, bg=bg)
        left_frame.pack(side=tk.LEFT, padx=(ph, 0), pady=pv)
        self._back_btn = gui_element_button_secondary(left_frame, locmsg("gui.back"), self._go_back)
        self._back_btn.pack(side=tk.LEFT)
        right_frame = tk.Frame(top_bar, bg=bg)
        right_frame.pack(side=tk.RIGHT, padx=(0, ph), pady=pv)
        self._save_btn = gui_element_button_primary(right_frame, locmsg("gui.save"), self._on_save)
        self._save_btn.pack(side=tk.LEFT, padx=(gh, 0))

    def set_model_key(self, model_key: str | None) -> None:
        self._model_key = model_key
        if self._detail is None:
            return
        model = self._manager.get_model(model_key) if model_key else None
        self._detail.set_model(model)
        self._update_save_button_state()
        self._update_page_heading()
        try:
            self.winfo_toplevel().title(self.get_screen_title())
        except tk.TclError:
            pass

    def _update_save_button_state(self) -> None:
        if self._save_btn is None:
            return
        state = tk.NORMAL if self._model_key else tk.DISABLED
        self._save_btn.configure(state=state)

    def _go_back(self) -> None:
        if self.on_back:
            self.on_back()

    def _on_save(self) -> None:
        if self._detail is None:
            return
        model_key = self._detail.get_model_key()
        if not model_key:
            return
        try:
            updates = self._detail.get_updates()
        except ValueError as exc:
            self._show_info(locmsg("models.detail.validation_title"), "", errors=[str(exc)])
            return
        updated = self._manager.update_model(model_key, **updates)
        if not updated:
            self._show_info(locmsg("models.detail.save_modal_title"), locmsg("models.detail.save_failed"))
            return
        self.set_model_key(model_key)
        self._show_info(locmsg("models.detail.save_modal_title"), locmsg("models.detail.save_ok"))

    def _show_info(
        self,
        title: str,
        message: str,
        *,
        errors: list[str] | None = None,
    ) -> None:
        if self._app_layout:
            self._app_layout.modals.show_info(title, message, errors=errors)
