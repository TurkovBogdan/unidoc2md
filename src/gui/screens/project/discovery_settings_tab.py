"""Таб «Файлы проекта»: настройки discovery и таблица файлов."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any

from src.modules.file_discovery import (
    DiscoveryService,
    FileDiscoveryPathNotFoundError,
)
from src.modules.file_discovery.models import DiscoveryConfig
from src.modules.file_extract import get_supported_extensions

from src.gui.template.components import CustomScrollbar
from src.gui.template.elements import gui_element_header_3
from src.gui.template.styles import FONT_FAMILY_UI, PALETTE, SPACING, UI_FONT_SIZE, UI_TABS
from src.gui.utils import open_folder


class DiscoverySettingsTab(ttk.Frame):
    """Кнопки открытия/обновления, рекурсивный поиск и таблица файлов."""

    SETTINGS_WIDTH_PX = 520
    _SEPARATOR_PADX = 12

    _DISCOVERY_ARTICLE = """
Файлы для обработки нужно поместить в папку документов проекта; открыть её можно кнопкой «Открыть документы».

После добавления файлов нажмите «Обновить», они должны появиться в таблице (если формат поддерживается приложением).

*При включении «Вложенные папки» поиск идёт рекурсивно; markdown сохраняется в аналогичную структуру каталогов.

Эта версия приложения умеет обрабатывать следующие форматы:
- pdf, docx (документы ms office), odt (документы open-office)
- png, jpg, webp, bmp, gif, tiff, svg
- txt, markdown

Со следующими форматами возникли сложности, но они в работе:
- doc (старый формат ms office), rtv (общий формат текстового документа) 

Поддержки презентаций (pptx), таблиц (xls, csv) сейчас так-же нет



""".strip()

    def __init__(self, parent: ttk.Frame, project_root: Path, **kwargs) -> None:
        super().__init__(parent, **kwargs)
        self._project_root = project_root
        self._file_discovery_recursive_var = tk.BooleanVar(value=False)
        self._file_search_tree: ttk.Treeview | None = None
        self._file_search_scrollbar: tk.Widget | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        padx, pady = UI_TABS["content_padding"]
        wrap = ttk.Frame(self)
        wrap.pack(fill=tk.BOTH, expand=True, padx=padx, pady=pady)

        left_frame = tk.Frame(wrap, width=self.SETTINGS_WIDTH_PX, bg=PALETTE["bg_surface"])
        left_frame.pack_propagate(False)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self._SEPARATOR_PADX))
        gui_element_header_3(left_frame, "Исходные документы")
        gap = SPACING["sm"]
        surf = PALETTE["bg_surface"]
        row = tk.Frame(left_frame, bg=surf)
        row.pack(fill=tk.X, pady=(0, gap))

        ttk.Button(
            row,
            text="Открыть документы",
            command=lambda: open_folder(self._project_root / "docs"),
            style="Secondary.TButton",
        ).pack(side=tk.LEFT)
        tk.Frame(row, width=gap, bg=surf).pack(side=tk.LEFT)

        ttk.Button(
            row,
            text="Обновить",
            command=self.refresh_table,
            style="Secondary.TButton",
        ).pack(side=tk.LEFT)
        tk.Frame(row, width=gap, bg=surf).pack(side=tk.LEFT)

        ttk.Checkbutton(
            row,
            variable=self._file_discovery_recursive_var,
            text="Вложенные папки",
            style="TCheckbutton",
        ).pack(side=tk.LEFT)

        self._file_discovery_recursive_var.trace_add("write", lambda *_: self.refresh_table())
        table_wrap = ttk.Frame(left_frame)
        table_wrap.pack(fill=tk.BOTH, expand=True)
        columns = ("filepath", "extension")
        self._file_search_tree = ttk.Treeview(
            table_wrap,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=12,
        )
        self._file_search_tree.heading("filepath", text="Имя файла")
        self._file_search_tree.heading("extension", text="Формат")
        self._file_search_tree.column("filepath", width=400, stretch=True, anchor=tk.W)
        self._file_search_tree.column("extension", width=80, stretch=False, anchor=tk.W)
        self._file_search_scrollbar = CustomScrollbar(table_wrap, command=self._file_search_tree.yview)
        self._file_search_tree.configure(yscrollcommand=self._file_search_scrollbar.set)
        self._file_search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._file_search_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
        self._article_text.insert(tk.END, self._DISCOVERY_ARTICLE)
        self._article_text.configure(state=tk.DISABLED)

    def refresh_table(self) -> None:
        """Заполняет таблицу файлов: отображаем все обнаруженные файлы поддерживаемых форматов.
        Настройки extract (алгоритм «Пропустить») не учитываются — фильтрация по skip только в Pipeline."""
        if not self._file_search_tree:
            return
        self._file_search_tree.delete(*self._file_search_tree.get_children())
        docs_dir = self._project_root / "docs"
        try:
            recursive = bool(self._file_discovery_recursive_var.get())
        except (TypeError, tk.TclError):
            recursive = False
        extensions = get_supported_extensions()
        if not extensions:
            extensions = {"*"}
        config = DiscoveryConfig(
            path=str(docs_dir),
            extensions=extensions,
            hash=False,
            recursive_search=recursive,
        )
        try:
            service = DiscoveryService()
            documents = service.discover_files(config)
        except FileDiscoveryPathNotFoundError:
            documents = []
        for i, doc in enumerate(documents):
            # folder уже нормализован относительно docs
            rel_str = doc.folder if doc.folder != "." else ""
            full_name = f"{doc.filename}{doc.extension}" if doc.extension else doc.filename
            name_with_path = f"{rel_str}/{full_name}".lstrip("/") if rel_str else full_name
            ext_display = (doc.extension or "").lstrip(".")
            self._file_search_tree.insert(
                "",
                tk.END,
                iid=f"f{i}",
                values=(name_with_path, ext_display),
            )

    def load_discovery(self, data: dict[str, Any] | None) -> None:
        """Заполняет виджеты из словаря discovery (recursive_search)."""
        data = data or {}
        self._file_discovery_recursive_var.set(bool(data.get("recursive_search", False)))

    def get_discovery_payload(self) -> dict[str, Any]:
        """Возвращает payload для секции discovery."""
        try:
            recursive = bool(self._file_discovery_recursive_var.get())
        except (TypeError, tk.TclError):
            recursive = False
        return {"recursive_search": recursive}
