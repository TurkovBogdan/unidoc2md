"""Экран настроек приложения (app.ini): Общее, Провайдеры LLM, Провайдеры OCR."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from src.gui.adapters import load_app_config_dict, save_app_config_dict
from src.gui.template.components import ScrollableFrame, StyledTabView
from src.gui.template.elements import (
    gui_element_button_primary,
    gui_element_button_secondary,
    gui_element_input_select,
    gui_element_input_spin,
    gui_element_input_text,
    gui_element_header_3,
    gui_element_page_title,
    gui_element_separator,
    gui_element_separator_vert,
)
from src.gui.screens.base_screen import BaseGUIScreen
from src.gui.template.styles import GUI_CONTENT_WRAPPER, GUI_TOPBAR

LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
PROVIDER_LABEL_WIDTH = 20
PROVIDER_ENTRY_WIDTH = 30
GATEWAY_TIMEOUT_MIN, GATEWAY_TIMEOUT_MAX = 1, 600

# LLM-провайдеры (секция llm_providers)
LLM_PROVIDER_SECTIONS = (
    ("anthropic", "Anthropic", ("anthropic_api_key",)),
    ("google", "Google", ("google_api_key",)),
    ("openai", "OpenAI", ("openai_api_key",)),
    ("xai", "XAI", ("xai_team_id", "xai_management_key", "xai_api_key")),
)


class SettingsScreen(BaseGUIScreen):
    """Настройки приложения: табы «Общее», «Провайдеры LLM», «Провайдеры OCR»."""

    SCREEN_CODE = "settings"
    SCREEN_TITLE = "unidoc2md | Настройки"

    def __init__(self, parent: ttk.Frame, app_root: Path, on_back, *, app_layout=None, **kwargs) -> None:
        super().__init__(parent, app_root=app_root, app_layout=app_layout, **kwargs)
        self.app_root = app_root
        self.on_back = on_back
        self._vars: dict[str, tk.StringVar | tk.BooleanVar] = {}
        self._provider_key_frames: dict[str, tk.Frame] = {}
        self._build_ui()
        self._load_config()

    def _on_llm_provider_enabled_change(self, provider_id: str) -> None:
        frame = self._provider_key_frames.get(provider_id)
        if not frame:
            return
        enabled_var = self._vars.get(f"llm_providers.{provider_id}_provider_enabled")
        if enabled_var and isinstance(enabled_var, tk.BooleanVar):
            if enabled_var.get():
                frame.grid()
            else:
                frame.grid_remove()

    def _on_yandex_ocr_enabled_change(self) -> None:
        frame = self._provider_key_frames.get("yandex_ocr")
        if not frame:
            return
        enabled_var = self._vars.get("yandex_ocr.provider_enabled")
        if enabled_var and isinstance(enabled_var, tk.BooleanVar):
            if enabled_var.get():
                frame.grid()
            else:
                frame.grid_remove()

    def _build_ui(self) -> None:
        self._top_panel()

        ph, pv = GUI_CONTENT_WRAPPER["padding"]
        content_wrap = tk.Frame(self, bg=GUI_CONTENT_WRAPPER["background"])
        content_wrap.pack(fill=tk.BOTH, expand=True, padx=(ph, ph), pady=(0, pv))

        gui_element_page_title(content_wrap, "Настройки")

        tab_view = StyledTabView(
            content_wrap,
            [
                ("general", "Общее"),
                ("llm_providers", "Провайдеры LLM"),
                ("ocr_providers", "Провайдеры OCR"),
            ],
            initial="general",
        )
        tab_view.pack(fill=tk.BOTH, expand=True)

        self._build_general_tab(tab_view.content_holder)
        self._build_llm_providers_tab(tab_view.content_holder)
        self._build_ocr_providers_tab(tab_view.content_holder)

        tab_view.add_tab_content("general", self._general_frame)
        tab_view.add_tab_content("llm_providers", self._llm_providers_scroll)
        tab_view.add_tab_content("ocr_providers", self._ocr_providers_scroll)

    def _build_general_tab(self, parent: ttk.Frame) -> None:
        """Таб «Общее»: ядро (debug, log_level)."""
        self._general_frame = ttk.Frame(parent)
        form = self._general_frame

        core_header = ttk.Frame(form)
        gui_element_header_3(core_header, "Ядро")
        core_header.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(10, 8))
        ttk.Label(form, text="Режим отладки:", width=PROVIDER_LABEL_WIDTH, anchor=tk.W).grid(
            row=1, column=0, sticky=tk.W, pady=2
        )
        debug_var = tk.BooleanVar(value=False)
        self._vars["core.debug"] = debug_var
        ttk.Checkbutton(form, variable=debug_var, text="Включить").grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=2
        )
        ttk.Label(form, text="Уровень логирования:", width=PROVIDER_LABEL_WIDTH, anchor=tk.W).grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        level_var = tk.StringVar()
        self._vars["log.level"] = level_var
        gui_element_input_select(
            form,
            variable=level_var,
            values=LOG_LEVELS,
            width=20,
        ).grid(row=2, column=1, padx=5, pady=2, sticky=tk.W)

    def _build_llm_providers_tab(self, parent: ttk.Frame) -> None:
        """Таб «Провайдеры LLM»."""
        self._llm_providers_scroll = ScrollableFrame(parent)
        form = ttk.Frame(self._llm_providers_scroll.content_frame)
        form.pack(fill=tk.BOTH, expand=True)

        # Общее — до настроек провайдеров
        general_header = ttk.Frame(form)
        gui_element_header_3(general_header, "Общее")
        general_header.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(10, 2))
        gateway_row = ttk.Frame(form)
        gateway_row.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))
        ttk.Label(gateway_row, text="Таймаут шлюза (сек):", width=PROVIDER_LABEL_WIDTH, anchor=tk.W).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        gateway_var = tk.StringVar(value="30")
        self._vars["llm_providers.gateway_timeout"] = gateway_var
        gui_element_input_spin(
            gateway_row,
            textvariable=gateway_var,
            from_=GATEWAY_TIMEOUT_MIN,
            to=GATEWAY_TIMEOUT_MAX,
            width=6,
        ).pack(side=tk.LEFT)

        def _render_llm_provider(
            parent_form: ttk.Frame,
            start_row: int,
            provider_id: str,
            group_name: str,
            keys: tuple[str, ...],
            first_in_row: bool = False,
        ) -> None:
            group_wrap = ttk.Frame(parent_form)
            gui_element_header_3(group_wrap, group_name)
            top_pady = 0 if first_in_row else 6
            group_wrap.grid(row=start_row, column=0, columnspan=2, sticky=tk.W, pady=(top_pady, 2))
            current_row = start_row + 1
            enabled_var = tk.BooleanVar(value=False)
            self._vars[f"llm_providers.{provider_id}_provider_enabled"] = enabled_var
            ttk.Checkbutton(
                parent_form,
                variable=enabled_var,
                text="Включить провайдер",
                command=lambda: self._on_llm_provider_enabled_change(provider_id),
            ).grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=2)
            current_row += 1

            key_frame = ttk.Frame(parent_form)
            key_frame.grid(row=current_row, column=0, columnspan=2, sticky=tk.W)
            self._provider_key_frames[provider_id] = key_frame
            for i, key in enumerate(keys):
                label = key.replace("_", " ").title()
                ttk.Label(
                    key_frame, text=f"{label}:", width=PROVIDER_LABEL_WIDTH, anchor=tk.W
                ).grid(row=i, column=0, sticky=tk.W, pady=2)
                var = tk.StringVar()
                self._vars[f"llm_providers.{key}"] = var
                entry = gui_element_input_text(
                    key_frame,
                    textvariable=var,
                    width=PROVIDER_ENTRY_WIDTH,
                )
                entry.grid(row=i, column=1, padx=5, pady=2, sticky=tk.W)

        # Сетка в 3 колонки: [ left | vert line | right ]; горизонтальный разделитель по ячейкам
        form.columnconfigure(0, weight=1)
        form.columnconfigure(2, weight=1)

        row = 2
        left_col = ttk.Frame(form)
        left_col.grid(row=row, column=0, sticky=tk.NW, pady=(10, 4), padx=(0, 8))
        sep = gui_element_separator_vert(form)
        sep.grid(row=row, column=1, sticky=tk.NS, padx=0, pady=(10, 4))
        right_col = ttk.Frame(form)
        right_col.grid(row=row, column=2, sticky=tk.NW, pady=(10, 4), padx=(8, 0))

        _render_llm_provider(left_col, 0, "anthropic", "Anthropic", ("anthropic_api_key",), first_in_row=True)
        _render_llm_provider(right_col, 0, "google", "Google", ("google_api_key",), first_in_row=True)
        row += 1

        sep_left_cell = ttk.Frame(form)
        gui_element_separator(sep_left_cell).pack(fill=tk.X)
        sep_left_cell.grid(row=row, column=0, sticky=tk.EW, pady=(4, 4))
        sep_right_cell = ttk.Frame(form)
        gui_element_separator(sep_right_cell).pack(fill=tk.X)
        sep_right_cell.grid(row=row, column=2, sticky=tk.EW, pady=(4, 4))
        row += 1

        left_col_2 = ttk.Frame(form)
        left_col_2.grid(row=row, column=0, sticky=tk.NW, pady=(0, 4), padx=(0, 8))
        sep_2 = gui_element_separator_vert(form)
        sep_2.grid(row=row, column=1, sticky=tk.NS, padx=0, pady=(0, 4))
        right_col_2 = ttk.Frame(form)
        right_col_2.grid(row=row, column=2, sticky=tk.NW, pady=(0, 4), padx=(8, 0))

        _render_llm_provider(left_col_2, 0, "openai", "OpenAI", ("openai_api_key",), first_in_row=True)
        _render_llm_provider(right_col_2, 0, "xai", "XAI", ("xai_team_id", "xai_management_key", "xai_api_key"), first_in_row=True)

    def _build_ocr_providers_tab(self, parent: ttk.Frame) -> None:
        """Таб «Провайдеры OCR»: Yandex OCR."""
        self._ocr_providers_scroll = ScrollableFrame(parent)
        form = ttk.Frame(self._ocr_providers_scroll.content_frame)
        form.pack(fill=tk.BOTH, expand=True)

        yo_frame = ttk.Frame(form)
        yo_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        yo_title = ttk.Frame(yo_frame)
        gui_element_header_3(yo_title, "Yandex OCR")
        yo_title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 2))
        enabled_var = tk.BooleanVar(value=False)
        self._vars["yandex_ocr.provider_enabled"] = enabled_var
        ttk.Checkbutton(
            yo_frame,
            variable=enabled_var,
            text="Включить Yandex OCR",
            command=self._on_yandex_ocr_enabled_change,
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        key_frame_yo = ttk.Frame(yo_frame)
        key_frame_yo.grid(row=2, column=0, columnspan=2, sticky=tk.W)
        self._provider_key_frames["yandex_ocr"] = key_frame_yo
        for i, key in enumerate(("key_id", "key_secret")):
            label = "Key ID" if key == "key_id" else "Key Secret"
            ttk.Label(key_frame_yo, text=f"{label}:", width=PROVIDER_LABEL_WIDTH, anchor=tk.W).grid(
                row=i, column=0, sticky=tk.W, pady=2
            )
            var = tk.StringVar()
            self._vars[f"yandex_ocr.{key}"] = var
            entry = gui_element_input_text(
                key_frame_yo,
                textvariable=var,
                width=PROVIDER_ENTRY_WIDTH,
            )
            entry.grid(row=i, column=1, padx=5, pady=2, sticky=tk.W)

    def _top_panel(self) -> None:
        ph, pv = GUI_TOPBAR["padding"]
        gh, _gv = GUI_TOPBAR["gap"]
        bg = GUI_TOPBAR["background"]
        top_bar = tk.Frame(self, bg=bg)
        top_bar.pack(fill=tk.X, pady=(0, pv))
        left_frame = tk.Frame(top_bar, bg=bg)
        left_frame.pack(side=tk.LEFT, padx=(ph, 0), pady=pv)
        gui_element_button_secondary(left_frame, "Назад", self._go_back).pack(
            side=tk.LEFT, padx=(0, gh)
        )
        gui_element_button_primary(left_frame, "Сохранить", self._save).pack(
            side=tk.LEFT, padx=(0, gh)
        )

    def _load_config(self) -> None:
        data = load_app_config_dict()
        lp = data.get("llm_providers") or {}
        yo = data.get("yandex_ocr") or {}
        core = data.get("core") or {}
        for key, var in self._vars.items():
            if key.startswith("llm_providers."):
                field = key.split(".", 1)[1]
                if field.endswith("_provider_enabled"):
                    var.set(lp.get(field, False))
                elif field == "gateway_timeout":
                    var.set(str(lp.get(field, 30)))
                else:
                    var.set(lp.get(field, ""))
            elif key.startswith("yandex_ocr."):
                field = key.split(".", 1)[1]
                if field == "provider_enabled":
                    var.set(yo.get(field, False))
                else:
                    var.set(yo.get(field, ""))
            elif key == "core.debug":
                var.set(core.get("debug", False))
            elif key == "log.level":
                var.set(core.get("log_level", "DEBUG"))
        for provider_id, _, _ in LLM_PROVIDER_SECTIONS:
            self._on_llm_provider_enabled_change(provider_id)
        self._on_yandex_ocr_enabled_change()

    def _get_form_data(self) -> dict:
        lp = {}
        yo = {}
        for key, var in self._vars.items():
            if key.startswith("llm_providers."):
                field = key.split(".", 1)[1]
                if isinstance(var, tk.BooleanVar):
                    lp[field] = var.get()
                elif field == "gateway_timeout":
                    try:
                        val = int(var.get() if isinstance(var, tk.StringVar) else 30)
                    except (TypeError, ValueError):
                        val = 30
                    lp[field] = max(GATEWAY_TIMEOUT_MIN, min(GATEWAY_TIMEOUT_MAX, val))
                else:
                    lp[field] = var.get() if isinstance(var, tk.StringVar) else ""
            elif key.startswith("yandex_ocr."):
                field = key.split(".", 1)[1]
                if isinstance(var, tk.BooleanVar):
                    yo[field] = var.get()
                else:
                    yo[field] = var.get() if isinstance(var, tk.StringVar) else ""
        core_debug = self._vars.get("core.debug")
        log_level = self._vars.get("log.level")
        return {
            "core": {
                "debug": core_debug.get() if isinstance(core_debug, tk.BooleanVar) else False,
                "log_level": (log_level.get() or "DEBUG").strip() if isinstance(log_level, tk.StringVar) else "DEBUG",
                "console_log_level": "INFO",
            },
            "llm_providers": lp,
            "yandex_ocr": yo,
        }

    def _save(self) -> None:
        data = self._get_form_data()
        # app.ini, AppConfigStore, хранилища модулей llm_providers и yandex_ocr (для немедленного эффекта)
        save_app_config_dict(data)
        if self._app_layout:
            self._app_layout.modals.show_info("Настройки", "Настройки сохранены.")

    def _go_back(self) -> None:
        if self.on_back:
            self.on_back()
