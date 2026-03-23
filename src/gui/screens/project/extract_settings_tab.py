"""Таб «Извлечение данных»: форма настроек extract по схеме (common + провайдеры)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from src.modules.file_extract import get_extract_settings_schema
from src.modules.file_extract.providers.file_extract_provider import get_provider_classes

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
    gui_element_input_spin,
    gui_element_separator,
    gui_element_text_small,
)
from src.gui.template.styles import (
    FONT_FAMILY_UI,
    PALETTE,
    UI_FONT_SIZE,
    UI_SETTINGS_BLOCK,
    UI_TABS,
)


class ExtractSettingsTab(ttk.Frame):
    """
    Скроллируемый контейнер с формой extract по SettingsSchemaCollection:
    опциональная группа common, затем провайдеры (все поля, первое — «Алгоритм работы»).
    Нормализацию payload выполняет вызывающий код через normalize_extract_payload.
    """

    def __init__(self, parent: ttk.Frame, project_root: Path, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._project_root = project_root
        self._has_extract_common_group = False
        self._extract_common_vars: dict[str, tk.Variable] = {}
        self._extract_common_types: dict[str, str] = {}
        self._extract_common_options: dict[str, list[tuple[str, str]]] = {}
        self._extract_provider_vars: dict[str, dict[str, tk.Variable]] = {}
        self._extract_provider_types: dict[str, dict[str, str]] = {}
        self._extract_provider_options: dict[str, dict[str, list[tuple[str, str]]]] = {}
        self._extract_provider_sub_frames: dict[str, tuple[ttk.Frame, int]] = {}
        self._extract_provider_algorithm_vars: dict[str, tk.Variable] = {}
        self._build_ui()

    SETTINGS_WIDTH_PX = 520
    _SEPARATOR_PADX = 12

    _EXTRACT_ARTICLE = """
Раздел «Извлечение данных» управляет настройкой получения контента документов.

Ключевая сложность при обработке различных форматов документов — непонятно что именно находится на изображениях, это может быть как скан текста, так и простое фото или сопроводительная схема.

Большая часть настроек связанна именно с обработкой изображений, если не хотите заморачиваться, оставьте значения по умолчанию — они подойдут для большинства сценариев. 

На что стоит обратить внимание:
- Масштаб рендера и размер изображений могут сильно сказываться на стоимости и времени распознавания изображений, не рекомендую выставлять значения выше ~1500px
- Если в PDF файлах у вас сканы документов, скорее всего в них сразу два слоя: и изображение и текстовый слой авто-распознавания (к примеру от сканеров hp). Часто в нём куча ошибок распознования текста, в PDF лучше использовать адаптивный режим или рендер всех страниц в изображения
- Если вы уверены что изображений в офисных документах нет, отключите обработку изображений, это позволит немного сэкономить на обработке     
""".strip()

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
        article_label = ttk.Label(right_frame, text="Пояснения", style="RightPanelTitle.TLabel")
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
        self._article_scrollbar = CustomScrollbar(article_container, command=self._article_text.yview)
        self._article_text.configure(yscrollcommand=self._article_scrollbar.set)
        self._article_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._article_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._article_text.configure(state=tk.NORMAL)
        self._article_text.insert(tk.END, self._EXTRACT_ARTICLE)
        self._article_text.configure(state=tk.DISABLED)

        self._build_form(self._scroll.content_frame)

    def _build_form(self, parent: tk.Misc) -> None:
        """Строит блок extract по схеме: группы с разделителями, у провайдеров все поля (первое — «Алгоритм работы»)."""
        cfg = UI_SETTINGS_BLOCK
        wrap_px = cfg["container_width_px"]
        collection = get_extract_settings_schema()
        block = SettingsBlock(parent)

        first_group = True
        for group in collection.groups:
            if group.code != "common":
                continue
            self._has_extract_common_group = True
            if not first_group:
                block.add_full_width_row(gui_element_separator(block.form))
            first_group = False
            block.add_full_width_row(
                gui_element_header_3(block.form, group.title, pack=False)
            )
            if group.description:
                block.add_comment(
                    gui_element_input_description(
                        block.form, group.description, wraplength=wrap_px
                    )
                )
            for f in group.fields:
                row_frame = block.add_field_row_frame()
                var, label_w, desc_w, value_w, _ = self._make_field_widgets(
                    row_frame, f, wrap_px, block.form
                )
                self._extract_common_vars[f.key] = var
                self._extract_common_types[f.key] = f.type
                if f.type == "select":
                    self._extract_common_options[f.key] = list(f.options)
                block.finish_field_row(row_frame, label_w, value_w)
                block.add_comment(desc_w)
            break

        provider_groups = [g for g in collection.groups if g.code != "common"]
        exts_by_code: dict[str, list[str]] = {}
        for cls in get_provider_classes():
            exts_by_code[cls.provider_code()] = sorted(cls.supported_extensions())

        for idx, group in enumerate(provider_groups):
            provider_code = group.code
            if idx > 0:
                block.add_full_width_row(gui_element_separator(block.form))
            self._extract_provider_vars[provider_code] = {}
            self._extract_provider_types[provider_code] = {}
            self._extract_provider_options[provider_code] = {}

            fields_list = list(group.fields)
            if not fields_list:
                header_row_frame = block.add_field_row_frame()
                header_label = gui_element_header_3(
                    header_row_frame, group.title, pack=False
                )
                block.finish_field_row(header_row_frame, header_label, ttk.Frame(header_row_frame))
                if group.description:
                    block.add_comment(
                        gui_element_input_description(
                            block.form, group.description, wraplength=wrap_px
                        )
                    )
                supported = ", ".join(exts_by_code.get(provider_code, []))
                block.add_comment(
                    gui_element_text_small(
                        block.form,
                        f"Поддерживаемые форматы: {supported}",
                        wraplength=wrap_px,
                    )
                )
                continue

            first_field = fields_list[0]
            header_row_frame = block.add_field_row_frame()
            header_label = gui_element_header_3(
                header_row_frame, group.title, pack=False
            )
            first_var, _, _desc_w, value_w, _ = self._make_field_widgets(
                header_row_frame, first_field, wrap_px, block.form
            )
            self._extract_provider_vars[provider_code][first_field.key] = first_var
            self._extract_provider_types[provider_code][first_field.key] = first_field.type
            if first_field.type == "select":
                self._extract_provider_options[provider_code][first_field.key] = list(first_field.options)
            block.finish_field_row(header_row_frame, header_label, value_w)

            intro_and_desc = [group.description] if group.description else []
            if getattr(first_field, "description", ""):
                intro_and_desc.append(first_field.description)
            if intro_and_desc:
                block.add_comment(
                    gui_element_input_description(
                        block.form, "\n\n".join(intro_and_desc), wraplength=wrap_px
                    )
                )

            sub, sub_frame, sub_row = block.begin_sub_block()
            self._extract_provider_sub_frames[provider_code] = (sub_frame, sub_row)
            self._extract_provider_algorithm_vars[provider_code] = first_var
            for f in fields_list[1:]:
                row_frame = sub.add_field_row_frame()
                var, label_w, desc_w, value_w, _ = self._make_field_widgets(
                    row_frame, f, wrap_px, sub._parent
                )
                self._extract_provider_vars[provider_code][f.key] = var
                self._extract_provider_types[provider_code][f.key] = f.type
                if f.type == "select":
                    self._extract_provider_options[provider_code][f.key] = list(f.options)
                sub.finish_field_row(row_frame, label_w, value_w)
                sub.add_comment(desc_w)

            supported = ", ".join(exts_by_code.get(provider_code, []))
            block.add_comment(
                gui_element_text_small(
                    block.form,
                    f"Поддерживаемые форматы: {supported}",
                    wraplength=wrap_px,
                )
            )

        for provider_code in self._extract_provider_algorithm_vars:
            self._update_provider_visibility(provider_code)
            self._extract_provider_algorithm_vars[provider_code].trace_add(
                "write", lambda *_, pc=provider_code: self._update_provider_visibility(pc)
            )

    ALGORITHM_KEY = "algorithm"
    SKIP_ALGORITHM_CODE = "skip"

    def _update_provider_visibility(self, provider_code: str) -> None:
        """Скрыть подблок настроек провайдера, если выбран алгоритм «Пропустить»."""
        frame_row = self._extract_provider_sub_frames.get(provider_code)
        algo_var = self._extract_provider_algorithm_vars.get(provider_code)
        if frame_row is None or algo_var is None:
            return
        frame, row = frame_row
        options = self._extract_provider_options.get(provider_code, {}).get(self.ALGORITHM_KEY, [])
        display = algo_var.get()
        code = next((c for c, d in options if d == display), "").strip().lower()
        if code == self.SKIP_ALGORITHM_CODE:
            frame.grid_remove()
        else:
            grid_sub_block(frame, row)

    def _make_field_widgets(
        self,
        row_parent: tk.Misc,
        f: Any,
        wraplength_px: int,
        form_for_desc: tk.Misc | None = None,
    ) -> tuple[tk.Variable, tk.Widget, tk.Widget | None, tk.Widget, bool]:
        """
        Создаёт виджеты для строки «Лейбл | поле» и описание под ней.
        row_parent — фрейм строки (лейбл и поле создаются в нём), form_for_desc — для описания.
        Возвращает (var, label_w, desc_w, value_w, is_bool).
        """
        desc = getattr(f, "description", "") or ""
        desc_parent = form_for_desc if form_for_desc is not None else row_parent
        if f.type == "bool":
            var = tk.BooleanVar(value=bool(f.default))
            label_w = gui_element_input_label(row_parent, f.label, wraplength=wraplength_px)
            cb = ttk.Checkbutton(row_parent, variable=var)
            label_w.bind(
                "<Button-1>",
                lambda e, v=var: v.set(not v.get()),
            )
            label_w.bind("<Enter>", lambda e, w=label_w: w.configure(cursor="hand2"))
            label_w.bind("<Leave>", lambda e, w=label_w: w.configure(cursor=""))
            return var, label_w, None, cb, True
        label_w = gui_element_input_label(row_parent, f.label, wraplength=wraplength_px)
        desc_w = gui_element_input_description(desc_parent, desc, wraplength=wraplength_px) if desc else None
        if f.type == "select":
            display_values = [d for _, d in f.options]
            default_display = next(
                (d for c, d in f.options if c == f.default),
                str(f.default),
            )
            var = tk.StringVar(value=default_display)
            value_w = gui_element_input_select(
                row_parent, variable=var, values=display_values, width=28
            )
        elif f.type == "int":
            var = tk.StringVar(value=str(f.default))
            value_w = gui_element_input_spin(
                row_parent, textvariable=var, from_=0, to=10000, width=10
            )
        else:
            var = tk.StringVar(value=str(f.default))
            value_w = ttk.Entry(row_parent, textvariable=var, width=30)
        return var, label_w, desc_w, value_w, False

    def load_extract(self, data: dict[str, Any] | None) -> None:
        """Заполняет виджеты из нормализованного payload extract (group_code -> values)."""
        data = data or {}
        common = data.get("common") or {}
        for key, var in self._extract_common_vars.items():
            val = common.get(key)
            typ = self._extract_common_types.get(key, "str")
            if val is None:
                continue
            try:
                if typ == "bool":
                    var.set(bool(val) if not isinstance(val, bool) else val)
                elif typ == "int":
                    var.set(str(int(val)) if val is not None else "0")
                elif typ == "select":
                    options = self._extract_common_options.get(key, [])
                    display = next((d for c, d in options if c == val), str(val))
                    var.set(display)
                else:
                    var.set(str(val) if val is not None else "")
            except (TypeError, ValueError, tk.TclError):
                pass
        for provider_code, var_dict in self._extract_provider_vars.items():
            prov = data.get(provider_code) or {}
            for key, var in var_dict.items():
                val = prov.get(key)
                typ = self._extract_provider_types.get(provider_code, {}).get(key, "str")
                if val is None:
                    continue
                try:
                    if typ == "bool":
                        var.set(bool(val) if not isinstance(val, bool) else val)
                    elif typ == "int":
                        var.set(str(int(val)) if val is not None else "0")
                    elif typ == "select":
                        options = self._extract_provider_options.get(provider_code, {}).get(key, [])
                        display = next((d for c, d in options if c == val), str(val))
                        var.set(display)
                    else:
                        var.set(str(val) if val is not None else "")
                except (TypeError, ValueError, tk.TclError):
                    pass
        for provider_code in self._extract_provider_algorithm_vars:
            self._update_provider_visibility(provider_code)

    def get_raw_extract_payload(self) -> dict[str, Any]:
        """Сырой extract payload (common + провайдеры); нормализацию выполняет вызывающий код."""
        common_payload: dict[str, Any] = {}
        for key, var in self._extract_common_vars.items():
            typ = self._extract_common_types.get(key, "str")
            try:
                raw = var.get()
                if typ == "bool":
                    common_payload[key] = bool(raw) if isinstance(raw, bool) else (
                        raw in (True, "true", "1", 1, "True")
                    )
                elif typ == "int":
                    common_payload[key] = int(raw) if raw not in (None, "") else 0
                elif typ == "select":
                    options = self._extract_common_options.get(key, [])
                    code = next(
                        (c for c, d in options if d == raw),
                        str(raw).strip() if raw is not None else "",
                    )
                    common_payload[key] = code
                else:
                    common_payload[key] = str(raw).strip() if raw is not None else ""
            except (TypeError, ValueError, tk.TclError):
                common_payload[key] = ""
        providers_payload: dict[str, dict[str, Any]] = {}
        for provider_code, var_dict in self._extract_provider_vars.items():
            prov: dict[str, Any] = {}
            types = self._extract_provider_types.get(provider_code, {})
            for key, var in var_dict.items():
                typ = types.get(key, "str")
                try:
                    raw = var.get()
                    if typ == "bool":
                        prov[key] = bool(raw) if isinstance(raw, bool) else (
                            raw in (True, "true", "1", 1, "True")
                        )
                    elif typ == "int":
                        prov[key] = int(raw) if raw not in (None, "") else 0
                    elif typ == "select":
                        options = self._extract_provider_options.get(provider_code, {}).get(key, [])
                        code = next(
                            (c for c, d in options if d == raw),
                            str(raw).strip() if raw is not None else "",
                        )
                        prov[key] = code
                    else:
                        prov[key] = str(raw).strip() if raw is not None else ""
                except (TypeError, ValueError, tk.TclError):
                    prov[key] = ""
            providers_payload[provider_code] = prov
        if self._has_extract_common_group:
            return {"common": common_payload, **providers_payload}
        return providers_payload
