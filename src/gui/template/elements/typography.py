"""Заголовки страницы и секций — единые элементы для всех экранов. Типографика из UI_TYPOGRAPHY (template/styles)."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.gui.template.styles import UI_INPUT_LABEL_DESCRIPTION, UI_TYPOGRAPHY


def gui_element_page_title(parent: tk.Misc, text: str) -> ttk.Label:
    """Заголовок страницы (крупный). Стиль и отступ из UI_TYPOGRAPHY["page_title"]."""
    t = UI_TYPOGRAPHY["page_title"]
    label = ttk.Label(parent, text=text, style="PageTitle.TLabel")
    label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_page_subtitle(parent: tk.Misc, text: str) -> ttk.Label:
    """Подзаголовок страницы. Стиль и отступ из UI_TYPOGRAPHY["page_subtitle"]."""
    t = UI_TYPOGRAPHY["page_subtitle"]
    label = ttk.Label(parent, text=text, style="PageSubtitle.TLabel")
    label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_header_2(parent: tk.Misc, text: str, *, pack: bool = True) -> ttk.Label:
    """Заголовок 2 уровня (секция). Стиль из UI_TYPOGRAPHY["header_2"]. При pack=True упаковывает в parent, иначе только возвращает виджет для grid."""
    t = UI_TYPOGRAPHY["header_2"]
    label = ttk.Label(parent, text=text, style="Header2.TLabel")
    if pack:
        label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_header_3(parent: tk.Misc, text: str, *, pack: bool = True) -> ttk.Label:
    """Заголовок 3 уровня (подсекция). Стиль из UI_TYPOGRAPHY["header_3"]. При pack=True упаковывает в parent, иначе только возвращает виджет для grid."""
    t = UI_TYPOGRAPHY["header_3"]
    label = ttk.Label(parent, text=text, style="Header3.TLabel")
    if pack:
        label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_header_3_light(parent: tk.Misc, text: str, *, pack: bool = True) -> ttk.Label:
    """Заголовок 3 уровня приглушённый (подсекция). Стиль из UI_TYPOGRAPHY["header_3_light"]. При pack=True упаковывает в parent, иначе только возвращает виджет для grid."""
    t = UI_TYPOGRAPHY["header_3_light"]
    label = ttk.Label(parent, text=text, style="Header3Light.TLabel")
    if pack:
        label.pack(anchor=tk.W, padx=0, pady=(0, t["pady_after"]))
    return label


def gui_element_input_label(
    parent: tk.Misc, text: str, wraplength: int | None = None
) -> ttk.Label:
    """
    Лейбл названия поля настройки. Стиль InputLabel.TLabel из UI_INPUT_LABEL_DESCRIPTION.
    Размещать в grid в колонке подписей. wraplength — ширина в px, по достижении текст переносится (фиксирует ширину колонки).
    """
    label = ttk.Label(parent, text=text, style="InputLabel.TLabel")
    if wraplength is not None:
        label.configure(wraplength=wraplength)
    return label


def gui_element_input_description(
    parent: tk.Misc, text: str, wraplength: int | None = None
) -> ttk.Label | None:
    """
    Описание поля настройки (приглушённый текст под лейблом). Опционально: при text == "" возвращает None.
    Стиль InputLabelDescription.TLabel. wraplength — ширина в px для переноса (колонка не резинится).
    """
    if not text:
        return None
    label = ttk.Label(parent, text=text, style="InputLabelDescription.TLabel")
    if wraplength is not None:
        label.configure(wraplength=wraplength)
    return label


def gui_element_text_small(
    parent: tk.Misc, text: str, wraplength: int | None = None
) -> ttk.Label:
    """
    Мелкий основной текст (цвет как у обычного текста, не приглушённый).
    Стиль BodySmall.TLabel (отдельный стиль, не общий с другими лейблами). wraplength — ширина в px для переноса.
    """
    label = ttk.Label(parent, text=text, style="BodySmall.TLabel")
    if wraplength is not None:
        label.configure(wraplength=wraplength)
    return label
