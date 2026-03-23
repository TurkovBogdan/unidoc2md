"""Деталка модели LLM-провайдера с редактированием полей реестра."""

from __future__ import annotations

from datetime import datetime
import tkinter as tk
from tkinter import ttk

from src.gui.adapters import LLMProviderModelRecord
from src.gui.template.elements.inputs import (
    gui_element_input_spin,
    gui_element_input_spin_float,
)
from src.gui.template.elements.typography import gui_element_header_3
from src.gui.template.elements.separator import gui_element_separator, gui_element_separator_vert
from src.gui.template.elements.warning_banner import gui_element_warning_banner
from src.gui.template.styles import SPACING

from .scrollable_frame import ScrollableFrame


class LLMProviderModelDetail(ttk.Frame):
    """Правая панель: отображение и редактирование выбранной модели."""

    LABEL_WIDTH = 18

    def __init__(self, parent: tk.Misc, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._model: LLMProviderModelRecord | None = None
        self._field_widgets: list[tk.Widget] = []
        self._boolean_vars = {
            "enabled": tk.BooleanVar(value=False),
            "input_text": tk.BooleanVar(value=False),
            "input_image": tk.BooleanVar(value=False),
            "input_audio": tk.BooleanVar(value=False),
            "input_video": tk.BooleanVar(value=False),
            "output_text": tk.BooleanVar(value=False),
            "output_image": tk.BooleanVar(value=False),
            "output_audio": tk.BooleanVar(value=False),
            "output_video": tk.BooleanVar(value=False),
            "chat": tk.BooleanVar(value=False),
            "function_calling": tk.BooleanVar(value=False),
            "structured_output": tk.BooleanVar(value=False),
            "reasoning": tk.BooleanVar(value=False),
        }
        self._provider_var = tk.StringVar(value="Не выбрано")
        self._code_var = tk.StringVar(value="Не выбрано")
        self._created_var = tk.StringVar(value="Не выбрано")
        self._context_window_var = tk.StringVar()
        self._price_input_var = tk.StringVar()
        self._price_output_var = tk.StringVar()
        self._build_ui()
        self.set_model(None)

    def _build_ui(self) -> None:
        self._empty_state = ttk.Frame(self)
        self._empty_state.pack(fill=tk.X, pady=(0, SPACING["sm"]))
        self._empty_banner = gui_element_warning_banner(
            self._empty_state,
            "Выберите модель слева, чтобы посмотреть и отредактировать её параметры.",
        )
        self._empty_banner.pack(fill=tk.X)

        self._scroll = ScrollableFrame(self)
        self._scroll.pack(fill=tk.BOTH, expand=True)
        self._form = ttk.Frame(self._scroll.content_frame)
        self._form.pack(fill=tk.BOTH, expand=True)
        self._build_form()

    def _build_form(self) -> None:
        self._form.columnconfigure(0, weight=1)
        self._form.columnconfigure(2, weight=1)

        row = 0
        info_col = ttk.Frame(self._form)
        info_col.grid(row=row, column=0, sticky=tk.NW, pady=(SPACING["sm"], SPACING["xs"]), padx=(0, SPACING["sm"]))
        top_sep = gui_element_separator_vert(self._form)
        top_sep.grid(row=row, column=1, sticky=tk.NS, pady=(SPACING["sm"], SPACING["xs"]))
        metrics_col = ttk.Frame(self._form)
        metrics_col.grid(row=row, column=2, sticky=tk.NW, pady=(SPACING["sm"], SPACING["xs"]), padx=(SPACING["sm"], 0))
        self._build_info_section(info_col)
        self._build_metrics_section(metrics_col)

        row += 1
        sep_left = ttk.Frame(self._form)
        gui_element_separator(sep_left).pack(fill=tk.X)
        sep_left.grid(row=row, column=0, sticky=tk.EW, pady=(0, SPACING["xs"]))
        sep_right = ttk.Frame(self._form)
        gui_element_separator(sep_right).pack(fill=tk.X)
        sep_right.grid(row=row, column=2, sticky=tk.EW, pady=(0, SPACING["xs"]))

        row += 1
        input_col = ttk.Frame(self._form)
        input_col.grid(row=row, column=0, sticky=tk.NW, pady=(0, SPACING["xs"]), padx=(0, SPACING["sm"]))
        support_sep = gui_element_separator_vert(self._form)
        support_sep.grid(row=row, column=1, sticky=tk.NS, pady=(0, SPACING["xs"]))
        output_col = ttk.Frame(self._form)
        output_col.grid(row=row, column=2, sticky=tk.NW, pady=(0, SPACING["xs"]), padx=(SPACING["sm"], 0))
        self._build_checkbox_section(
            input_col,
            "Поддержка входа",
            (
                ("input_text", "Принимает текст"),
                ("input_image", "Принимает изображения"),
                ("input_audio", "Принимает аудио"),
                ("input_video", "Принимает видео"),
            ),
        )
        self._build_checkbox_section(
            output_col,
            "Поддержка выхода",
            (
                ("output_text", "Возвращает текст"),
                ("output_image", "Возвращает изображения"),
                ("output_audio", "Возвращает аудио"),
                ("output_video", "Возвращает видео"),
            ),
        )

        row += 1
        features_sep = ttk.Frame(self._form)
        gui_element_separator(features_sep).pack(fill=tk.X)
        features_sep.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(0, SPACING["xs"]))

        row += 1
        features_col = ttk.Frame(self._form)
        features_col.grid(row=row, column=0, columnspan=3, sticky=tk.NW)
        self._build_checkbox_section(
            features_col,
            "Дополнительные функции",
            (
                ("chat", "Поддерживает чат"),
                ("function_calling", "Function calling"),
                ("structured_output", "Structured output"),
                ("reasoning", "Reasoning"),
            ),
        )

    def _add_info_row(self, parent: ttk.Frame, row: int, label: str, value_var: tk.StringVar) -> None:
        ttk.Label(parent, text=f"{label}:", anchor=tk.W).grid(
            row=row,
            column=0,
            sticky=tk.W,
            padx=(0, SPACING["sm"]),
            pady=SPACING["xs"],
            ipadx=0,
        )
        ttk.Label(parent, textvariable=value_var, anchor=tk.W).grid(
            row=row,
            column=1,
            sticky=tk.W,
            pady=SPACING["xs"],
        )

    def _build_info_section(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(1, weight=1)
        title_wrap = ttk.Frame(parent)
        gui_element_header_3(title_wrap, "Информация о модели")
        title_wrap.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, SPACING["xs"]))
        self._add_info_row(parent, 1, "Провайдер", self._provider_var)
        self._add_info_row(parent, 2, "Модель", self._code_var)
        self._add_info_row(parent, 3, "Создана", self._created_var)
        enabled_widget = ttk.Checkbutton(parent, variable=self._boolean_vars["enabled"], text="Включена")
        enabled_widget.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=SPACING["xs"])
        self._field_widgets.append(enabled_widget)

    def _build_metrics_section(self, parent: ttk.Frame) -> None:
        title_wrap = ttk.Frame(parent)
        gui_element_header_3(title_wrap, "Лимиты и цены")
        title_wrap.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, SPACING["xs"]))
        # Контекстное окно — int (спинбокс)
        ttk.Label(parent, text="Контекстное окно:", width=self.LABEL_WIDTH, anchor=tk.W).grid(
            row=1, column=0, sticky=tk.W, pady=SPACING["xs"]
        )
        context_spin = gui_element_input_spin(
            parent,
            textvariable=self._context_window_var,
            from_=0,
            to=20_000_000,
            increment=1000,
            width=10,
        )
        context_spin.grid(row=1, column=1, sticky=tk.W, padx=(SPACING["sm"], 0), pady=SPACING["xs"])
        self._field_widgets.append(context_spin._entry)
        # Цена входа — float (спинбокс)
        ttk.Label(parent, text="Цена входа / 1M:", width=self.LABEL_WIDTH, anchor=tk.W).grid(
            row=2, column=0, sticky=tk.W, pady=SPACING["xs"]
        )
        price_in_spin = gui_element_input_spin_float(
            parent,
            textvariable=self._price_input_var,
            from_=0.0,
            to=10_000.0,
            increment=0.1,
            width=10,
            decimals=4,
        )
        price_in_spin.grid(row=2, column=1, sticky=tk.W, padx=(SPACING["sm"], 0), pady=SPACING["xs"])
        self._field_widgets.append(price_in_spin._entry)
        # Цена выхода — float (спинбокс)
        ttk.Label(parent, text="Цена выхода / 1M:", width=self.LABEL_WIDTH, anchor=tk.W).grid(
            row=3, column=0, sticky=tk.W, pady=SPACING["xs"]
        )
        price_out_spin = gui_element_input_spin_float(
            parent,
            textvariable=self._price_output_var,
            from_=0.0,
            to=10_000.0,
            increment=0.1,
            width=10,
            decimals=4,
        )
        price_out_spin.grid(row=3, column=1, sticky=tk.W, padx=(SPACING["sm"], 0), pady=SPACING["xs"])
        self._field_widgets.append(price_out_spin._entry)

    def _build_checkbox_section(
        self,
        parent: ttk.Frame,
        title: str,
        items: tuple[tuple[str, str], ...],
    ) -> None:
        title_wrap = ttk.Frame(parent)
        gui_element_header_3(title_wrap, title)
        title_wrap.grid(row=0, column=0, sticky=tk.W, pady=(0, SPACING["xs"]))
        row = 1
        for field_name, label in items:
            widget = ttk.Checkbutton(parent, variable=self._boolean_vars[field_name], text=label)
            widget.grid(row=row, column=0, sticky=tk.W, pady=SPACING["xs"])
            self._field_widgets.append(widget)
            row += 1

    def set_model(self, model: LLMProviderModelRecord | None) -> None:
        self._model = model
        if model is None:
            self._provider_var.set("Не выбрано")
            self._code_var.set("Не выбрано")
            self._created_var.set("Не выбрано")
            self._context_window_var.set("")
            self._price_input_var.set("")
            self._price_output_var.set("")
            for var in self._boolean_vars.values():
                var.set(False)
            self._set_form_state(enabled=False)
            self._empty_state.pack(fill=tk.X, pady=(0, SPACING["sm"]))
            return

        self._provider_var.set(model.provider_code)
        self._code_var.set(model.code)
        self._created_var.set(self._format_created(model.created))
        self._boolean_vars["enabled"].set(model.enabled)
        self._boolean_vars["input_text"].set(model.input_text)
        self._boolean_vars["input_image"].set(model.input_image)
        self._boolean_vars["input_audio"].set(model.input_audio)
        self._boolean_vars["input_video"].set(model.input_video)
        self._boolean_vars["output_text"].set(model.output_text)
        self._boolean_vars["output_image"].set(model.output_image)
        self._boolean_vars["output_audio"].set(model.output_audio)
        self._boolean_vars["output_video"].set(model.output_video)
        self._boolean_vars["chat"].set(model.chat)
        self._boolean_vars["function_calling"].set(model.function_calling)
        self._boolean_vars["structured_output"].set(model.structured_output)
        self._boolean_vars["reasoning"].set(model.reasoning)
        self._context_window_var.set(self._stringify_optional(model.context_window))
        self._price_input_var.set(self._stringify_optional(model.price_input))
        self._price_output_var.set(self._stringify_optional(model.price_output))
        self._set_form_state(enabled=True)
        self._empty_state.pack_forget()

    def get_model_key(self) -> str | None:
        if self._model is None:
            return None
        return self._model.model_key

    def get_updates(self) -> dict[str, object]:
        if self._model is None:
            return {}
        return {
            "enabled": self._boolean_vars["enabled"].get(),
            "input_text": self._boolean_vars["input_text"].get(),
            "input_image": self._boolean_vars["input_image"].get(),
            "input_audio": self._boolean_vars["input_audio"].get(),
            "input_video": self._boolean_vars["input_video"].get(),
            "output_text": self._boolean_vars["output_text"].get(),
            "output_image": self._boolean_vars["output_image"].get(),
            "output_audio": self._boolean_vars["output_audio"].get(),
            "output_video": self._boolean_vars["output_video"].get(),
            "chat": self._boolean_vars["chat"].get(),
            "function_calling": self._boolean_vars["function_calling"].get(),
            "structured_output": self._boolean_vars["structured_output"].get(),
            "reasoning": self._boolean_vars["reasoning"].get(),
            "context_window": self._parse_optional_int_from_number(
                self._context_window_var.get(),
                "Контекстное окно",
            ),
            "price_input": self._parse_optional_float(
                self._price_input_var.get(),
                "Цена входа / 1M",
            ),
            "price_output": self._parse_optional_float(
                self._price_output_var.get(),
                "Цена выхода / 1M",
            ),
        }

    def _set_form_state(self, *, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for widget in self._field_widgets:
            try:
                widget.configure(state=state)
            except tk.TclError:
                continue

    @staticmethod
    def _format_created(value: int | None) -> str:
        if value in (None, ""):
            return "Не задано"
        try:
            return datetime.fromtimestamp(int(value)).strftime("%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError, OSError):
            return str(value)

    @staticmethod
    def _stringify_optional(value: object) -> str:
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _parse_optional_int(value: str, field_label: str) -> int | None:
        text = (value or "").strip()
        if not text:
            return None
        try:
            return int(text)
        except ValueError as exc:
            raise ValueError(f"{field_label}: ожидается целое число.") from exc

    @staticmethod
    def _parse_optional_int_from_number(value: str, field_label: str) -> int | None:
        """Парсит число (int или float-строка) и возвращает int. Как у полей цен — единый формат ввода."""
        text = (value or "").strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError as exc:
            raise ValueError(f"{field_label}: ожидается число.") from exc

    @staticmethod
    def _parse_optional_float(value: str, field_label: str) -> float | None:
        text = (value or "").strip()
        if not text:
            return None
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"{field_label}: ожидается число.") from exc
