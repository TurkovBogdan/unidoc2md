"""Extract tab: dynamic extract form from schema (common + per-provider groups)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from src.core import locmsg
from src.modules.file_extract import get_extract_settings_schema
from src.modules.file_extract.providers.file_extract_provider import get_provider_classes

from src.gui.screens.project.extract_locale_keys import (
    field_description,
    field_label,
    field_option,
    field_option_description,
    provider_description_key,
    provider_title_key,
)
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
    UI_RIGHT_PANEL_NOTES_TITLE_PADY,
    UI_SETTINGS_BLOCK,
    UI_TABS,
)


class ExtractSettingsTab(ttk.Frame):
    """
    Scrollable extract form from SettingsSchemaCollection: optional common group,
    then providers (all fields; first field is the algorithm).
    Schema carries codes only; UI strings use locmsg() via extract_locale_keys.
    """

    _COMMON_GROUP_CODE = "common"

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
        self._extract_provider_algorithm_desc_labels: dict[str, ttk.Label] = {}
        self._article_title_label: ttk.Label | None = None
        self._build_ui()

    SETTINGS_WIDTH_PX = 520
    _SEPARATOR_PADX = 12

    @staticmethod
    def _t(msgid: str) -> str:
        return locmsg(msgid)

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
        self._article_title_label = ttk.Label(
            right_frame, text=self._t("project_extract.notes_title"), style="RightPanelTitle.TLabel"
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
        self._article_text.insert(tk.END, self._t("project_extract.article"))
        self._article_text.configure(state=tk.DISABLED)

        self._build_form(self._scroll.content_frame)

    def refresh_locale(self) -> None:
        """Rebuild form and article after language change; preserve current widget values."""
        try:
            payload = self.get_raw_extract_payload()
            for child in self._scroll.content_frame.winfo_children():
                child.destroy()
            self._has_extract_common_group = False
            self._extract_common_vars = {}
            self._extract_common_types = {}
            self._extract_common_options = {}
            self._extract_provider_vars = {}
            self._extract_provider_types = {}
            self._extract_provider_options = {}
            self._extract_provider_sub_frames = {}
            self._extract_provider_algorithm_vars = {}
            self._extract_provider_algorithm_desc_labels = {}
            self._build_form(self._scroll.content_frame)
            if self._article_title_label is not None and self._article_title_label.winfo_exists():
                self._article_title_label.configure(text=self._t("project_extract.notes_title"))
            self._article_text.configure(state=tk.NORMAL)
            self._article_text.delete("1.0", tk.END)
            self._article_text.insert(tk.END, self._t("project_extract.article"))
            self._article_text.configure(state=tk.DISABLED)
            self.load_extract(payload)
        except tk.TclError:
            pass

    def _build_form(self, parent: tk.Misc) -> None:
        """Build extract UI from schema: separated groups; per provider, first field is algorithm."""
        cfg = UI_SETTINGS_BLOCK
        wrap_px = cfg["container_width_px"]
        collection = get_extract_settings_schema()
        block = SettingsBlock(parent)

        first_group = True
        for group in collection.groups:
            if group.code != self._COMMON_GROUP_CODE:
                continue
            self._has_extract_common_group = True
            if not first_group:
                block.add_full_width_row(gui_element_separator(block.form))
            first_group = False
            block.add_full_width_row(
                gui_element_header_3(block.form, self._t(provider_title_key(group.code)), pack=False)
            )
            if group.description:
                block.add_comment(
                    gui_element_input_description(
                        block.form, self._t(provider_description_key(group.code)), wraplength=wrap_px
                    )
                )
            for f in group.fields:
                row_frame = block.add_field_row_frame()
                var, label_w, desc_w, value_w, _ = self._make_field_widgets(
                    row_frame, f, wrap_px, block.form, group.code, include_description=True
                )
                self._extract_common_vars[f.key] = var
                self._extract_common_types[f.key] = f.type
                if f.type == "select":
                    self._extract_common_options[f.key] = list(f.options)
                block.finish_field_row(row_frame, label_w, value_w)
                block.add_comment(desc_w)
            break

        provider_groups = [g for g in collection.groups if g.code != self._COMMON_GROUP_CODE]
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
                block.add_full_width_row(
                    gui_element_header_3(block.form, self._t(provider_title_key(provider_code)), pack=False)
                )
                prov_intro_nf = self._t(provider_description_key(provider_code)).strip()
                if prov_intro_nf:
                    pil = gui_element_input_description(
                        block.form, prov_intro_nf, wraplength=wrap_px
                    )
                    if pil is not None:
                        block.add_comment(pil)
                supported = ", ".join(exts_by_code.get(provider_code, []))
                block.add_comment(
                    gui_element_text_small(
                        block.form,
                        self._t("project_extract.supported_formats").format(formats=supported),
                        wraplength=wrap_px,
                    )
                )
                continue

            block.add_full_width_row(
                gui_element_header_3(block.form, self._t(provider_title_key(provider_code)), pack=False)
            )
            prov_intro = self._t(provider_description_key(provider_code)).strip()
            if prov_intro:
                prov_intro_lbl = gui_element_input_description(
                    block.form, prov_intro, wraplength=wrap_px
                )
                if prov_intro_lbl is not None:
                    block.add_comment(prov_intro_lbl)
            first_field = fields_list[0]
            algo_row_frame = block.add_field_row_frame()
            first_var, label_w, _desc_w, value_w, _ = self._make_field_widgets(
                algo_row_frame, first_field, wrap_px, block.form, provider_code, include_description=False
            )
            self._extract_provider_vars[provider_code][first_field.key] = first_var
            self._extract_provider_types[provider_code][first_field.key] = first_field.type
            if first_field.type == "select":
                self._extract_provider_options[provider_code][first_field.key] = list(first_field.options)
            block.finish_field_row(algo_row_frame, label_w, value_w)

            algo_desc_lbl = gui_element_input_description(
                block.form, "\u200b", wraplength=wrap_px
            )
            if algo_desc_lbl is not None:
                self._extract_provider_algorithm_desc_labels[provider_code] = algo_desc_lbl
                block.add_comment(algo_desc_lbl)

            sub, sub_frame, sub_row = block.begin_sub_block()
            self._extract_provider_sub_frames[provider_code] = (sub_frame, sub_row)
            self._extract_provider_algorithm_vars[provider_code] = first_var
            for f in fields_list[1:]:
                row_frame = sub.add_field_row_frame()
                var, label_w, desc_w, value_w, _ = self._make_field_widgets(
                    row_frame, f, wrap_px, sub._parent, provider_code, include_description=True
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
                    self._t("project_extract.supported_formats").format(formats=supported),
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

    def _refresh_algorithm_description(self, provider_code: str) -> None:
        """Под выпадающим списком алгоритма: только описание выбранной опции (вступление провайдера — под заголовком)."""
        label_w = self._extract_provider_algorithm_desc_labels.get(provider_code)
        algo_var = self._extract_provider_algorithm_vars.get(provider_code)
        if label_w is None or algo_var is None:
            return
        try:
            if not label_w.winfo_exists():
                return
        except tk.TclError:
            return
        options = self._extract_provider_options.get(provider_code, {}).get(self.ALGORITHM_KEY, [])
        display = algo_var.get()
        code = self._code_from_select_display(
            provider_code, self.ALGORITHM_KEY, options, str(display)
        ).lower()
        opt_key = field_option_description(provider_code, self.ALGORITHM_KEY, code)
        opt_txt = self._t(opt_key)
        if opt_txt == opt_key:
            opt_txt = self._t(field_description(provider_code, self.ALGORITHM_KEY)).strip()
        else:
            opt_txt = opt_txt.strip()
        label_w.configure(text=opt_txt if opt_txt else "\u200b")

    def _code_from_select_display(
        self,
        provider_code: str,
        field_key: str,
        options: list[tuple[str, str]],
        display: str,
    ) -> str:
        disp = (display or "").strip()
        for value_code, opt_code in options:
            if self._t(field_option(provider_code, field_key, opt_code)) == disp:
                return value_code.strip()
        for value_code, opt_code in options:
            if opt_code == disp or value_code == disp:
                return value_code.strip()
        return disp

    def _update_provider_visibility(self, provider_code: str) -> None:
        """Hide provider sub-block when algorithm is «skip»."""
        self._refresh_algorithm_description(provider_code)
        frame_row = self._extract_provider_sub_frames.get(provider_code)
        algo_var = self._extract_provider_algorithm_vars.get(provider_code)
        if frame_row is None or algo_var is None:
            return
        frame, row = frame_row
        options = self._extract_provider_options.get(provider_code, {}).get(self.ALGORITHM_KEY, [])
        display = algo_var.get()
        code = self._code_from_select_display(
            provider_code, self.ALGORITHM_KEY, options, str(display)
        ).lower()
        if code == self.SKIP_ALGORITHM_CODE:
            frame.grid_remove()
        else:
            grid_sub_block(frame, row)

    def _make_field_widgets(
        self,
        row_parent: tk.Misc,
        f: Any,
        wraplength_px: int,
        form_for_desc: tk.Misc | None,
        provider_code: str,
        *,
        include_description: bool = True,
    ) -> tuple[tk.Variable, tk.Widget, tk.Widget | None, tk.Widget, bool]:
        """Build label | field row and optional description below.

        Labels use field keys (f.key), not schema f.label.
        """
        desc_parent = form_for_desc if form_for_desc is not None else row_parent
        label_resolved = self._t(field_label(provider_code, f.key))
        desc_text = self._t(field_description(provider_code, f.key)) if include_description else ""
        if f.type == "bool":
            var = tk.BooleanVar(value=bool(f.default))
            label_w = gui_element_input_label(row_parent, label_resolved, wraplength=wraplength_px)
            cb = ttk.Checkbutton(row_parent, variable=var)
            label_w.bind(
                "<Button-1>",
                lambda e, v=var: v.set(not v.get()),
            )
            label_w.bind("<Enter>", lambda e, w=label_w: w.configure(cursor="hand2"))
            label_w.bind("<Leave>", lambda e, w=label_w: w.configure(cursor=""))
            return var, label_w, None, cb, True
        label_w = gui_element_input_label(row_parent, label_resolved, wraplength=wraplength_px)
        desc_w = (
            gui_element_input_description(desc_parent, desc_text, wraplength=wraplength_px)
            if include_description
            else None
        )
        if f.type == "select":
            display_values = [
                self._t(field_option(provider_code, f.key, opt_code)) for _, opt_code in f.options
            ]
            default_display = next(
                (
                    self._t(field_option(provider_code, f.key, code))
                    for code, _ in f.options
                    if code == f.default
                ),
                self._t(field_option(provider_code, f.key, f.options[0][0])) if f.options else str(f.default),
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
        """Load widgets from normalized extract payload (group_code -> values)."""
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
                    display = next(
                        (
                            self._t(field_option(self._COMMON_GROUP_CODE, key, code))
                            for code, _ in options
                            if code == val
                        ),
                        str(val),
                    )
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
                        display = next(
                            (
                                self._t(field_option(provider_code, key, code))
                                for code, _ in options
                                if code == val
                            ),
                            str(val),
                        )
                        var.set(display)
                    else:
                        var.set(str(val) if val is not None else "")
                except (TypeError, ValueError, tk.TclError):
                    pass
        for provider_code in self._extract_provider_algorithm_vars:
            self._update_provider_visibility(provider_code)

    def get_raw_extract_payload(self) -> dict[str, Any]:
        """Raw extract payload (common + providers); caller normalizes."""
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
                    common_payload[key] = self._code_from_select_display(
                        self._COMMON_GROUP_CODE, key, options, str(raw)
                    )
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
                        prov[key] = self._code_from_select_display(
                            provider_code, key, options, str(raw)
                        )
                    else:
                        prov[key] = str(raw).strip() if raw is not None else ""
                except (TypeError, ValueError, tk.TclError):
                    prov[key] = ""
            providers_payload[provider_code] = prov
        if self._has_extract_common_group:
            return {"common": common_payload, **providers_payload}
        return providers_payload
