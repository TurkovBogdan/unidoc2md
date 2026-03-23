"""
Стилизация ttk: тема, цвета, отступы. Подключение темы к root — gui_setup_theme(root) в template/styles.

Правило: ВСЕ параметры стилей (цвета, размеры, отступы, шрифты и т.п.) задаются
только в этом файле — src/gui/template/styles/theme.py. В компонентах, элементах и экранах
не хардкодить числа/цвета: брать из PALETTE, UI_*, констант этого модуля.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# -----------------------------------------------------------------------------
# Основные цвета — префикс STL_COLOR_<логика>. PALETTE / STL_COLORS ниже.
# -----------------------------------------------------------------------------

# Background
STL_COLOR_BG = "#0f1410"
STL_COLOR_BG_SURFACE = "#1a2218"
STL_COLOR_BG_ELEVATED = "#293628"
STL_COLOR_MODAL_OVERLAY = "#080808"

# Text
STL_COLOR_TEXT_PRIMARY = "#d8e4d6"
STL_COLOR_TEXT_SOFT = "#a8b8a4"  # между primary и muted, слегка приглушённый
STL_COLOR_TEXT_MUTED = "#7a8f76"

# Selection (фон и текст выделения)
STL_COLOR_SELECT_BACKGROUND = "#2d4a2d"
STL_COLOR_SELECT_TEXT = "#e0ece0"

# Border
STL_COLOR_BORDER = "#2d352d"
STL_COLOR_BORDER_INPUT = "#3a4b39"

# Scrollbar: фон чуть светлее bg_surface, ползунок как панели (bg_elevated)
STL_COLOR_SCROLL_TROUGH = "#1e261c"
STL_COLOR_SCROLL_THUMB = STL_COLOR_BG_ELEVATED
STL_COLOR_SCROLL_HOVER = "#334332"

# -----------------------------------------------------------------------------
# Элементы интерфейса (кнопки): PRIMARY, SECONDARY, GHOST, DISABLED.
# В каждой группе: базовый цвет, наведение, нажатие, цвет текста.
# -----------------------------------------------------------------------------

# PRIMARY — основное действие
UI_COLOR_PRIMARY = "#457045"
UI_COLOR_PRIMARY_HOVER = "#5d9a5d"  # ярче при наведении
UI_COLOR_PRIMARY_PRESSED = "#345834"
UI_COLOR_PRIMARY_TEXT = "#d8e4d6"

# SECONDARY — вторичное действие (светлее фона, чуть темнее Primary)
UI_COLOR_SECONDARY = "#364a36"
UI_COLOR_SECONDARY_HOVER = "#4a634a"  # ярче при наведении
UI_COLOR_SECONDARY_PRESSED = "#2d3d2d"
UI_COLOR_SECONDARY_TEXT = "#d8e4d6"

# GHOST — неважное действие (как Secondary по тону, но с уходом в серый)
UI_COLOR_GHOST = "#242624"
UI_COLOR_GHOST_HOVER = "#2a2c2a"
UI_COLOR_GHOST_PRESSED = "#1e201e"
UI_COLOR_GHOST_TEXT = "#d8e4d6"

# DISABLED — отключённое состояние
UI_COLOR_DISABLED = "#232d20"
UI_COLOR_DISABLED_HOVER = "#232d20"
UI_COLOR_DISABLED_PRESSED = "#232d20"
UI_COLOR_DISABLED_TEXT = "#7a8f76"

# Табы: цвета (как Primary/Secondary кнопки), отступы подписи и контента.
# content_padding — (padx, pady) контейнера таба: только сверху и снизу, без отступов слева/справа.
UI_TABS = {
    "active": UI_COLOR_PRIMARY,
    "inactive": UI_COLOR_SECONDARY,
    "hover": UI_COLOR_PRIMARY_HOVER,
    "pressed": UI_COLOR_PRIMARY_PRESSED,
    "inactive_hover": UI_COLOR_SECONDARY_HOVER,
    "inactive_pressed": UI_COLOR_SECONDARY_PRESSED,
    "underline": STL_COLOR_BORDER,  # линия под панелью табов
    "gap_px": 8,
    "bar_padding_y": 2,
    "margin_after_line_px": 8,
    "item_padx": 10,  # как UI_BUTTONS["padding"][0]
    "item_pady": 6,   # как UI_BUTTONS["padding"][1]
    "underline_height_px": 1,
    "content_padding": (0, 12),  # (padx, pady): только сверху и снизу
    "content_first_row_pady_top": 8,  # отступ сверху перед первой строкой контента (единый для всех табов)
}

PALETTE = STL_COLORS = {
    "bg_main": STL_COLOR_BG,
    "bg_surface": STL_COLOR_BG_SURFACE,
    "bg_elevated": STL_COLOR_BG_ELEVATED,
    "text_primary": STL_COLOR_TEXT_PRIMARY,
    "text_soft": STL_COLOR_TEXT_SOFT,
    "text_muted": STL_COLOR_TEXT_MUTED,
    "border": STL_COLOR_BORDER,
    "border_input": STL_COLOR_BORDER_INPUT,
    "select_bg": STL_COLOR_SELECT_BACKGROUND,
    "select_fg": STL_COLOR_SELECT_TEXT,
    "scrollbar_trough": STL_COLOR_SCROLL_TROUGH,
    "scrollbar_thumb": STL_COLOR_SCROLL_THUMB,
    "scrollbar_hover": STL_COLOR_SCROLL_HOVER,
    "separator": STL_COLOR_BORDER,
    "tab_active": UI_TABS["active"],
    "tab_inactive": UI_TABS["inactive"],
    "tab_hover": UI_TABS["hover"],
    "tab_pressed": UI_TABS["pressed"],
    "tab_inactive_hover": UI_TABS["inactive_hover"],
    "tab_inactive_pressed": UI_TABS["inactive_pressed"],
    "modal_overlay": STL_COLOR_MODAL_OVERLAY,
}

# Шрифты: задаются в gui_setup_theme (template.styles) из bootstrap или fallback; один шрифт для UI и моно.
FONT_FAMILY_UI = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

# Размеры шрифтов в пунктах. В font=() использовать UI_FONT_SIZE["ключ"], не хардкодить числа.
UI_FONT_SIZE = {
    "extra_small": 9,
    "small": 10,
    "medium": 12,
    "large": 14,
    "extra_large": 16,
}


# Кнопки: отступы, без рамки и без видимой обводки фокуса.
# font_size — ключ UI_FONT_SIZE для текста кнопок.
UI_BUTTONS = {
    "padding": (10, 6),
    "borderwidth": 0,
    "relief": "flat",
    "font_size": "small",
    "focuswidth": 0,
    "cursor": "hand2",
    "cursor_leave": "",
    "highlight_thickness": 0,
}

# Поля ввода: ttk и кастомные tk-элементы. Один источник истины для всех инпутов проекта.
# font_size — ключ UI_FONT_SIZE для текста в полях ввода (Entry, Spinbox, Combobox и т.п.).
UI_INPUTS = {
    "font_size": "small",
    "borderwidth": 1,
    "relief": "flat",
    "entry_layout_border": "1",  # толщина бордера в layout TEntry
    "padding": (4, 2),  # отступы внутри поля для Combobox / Spinbox
    "entry_padding": (0, 0),  # TEntry: убираем внутреннюю рамку-эффект вокруг текста
    # ключи PALETTE для стандартных ttk-элементов
    "field_background": "bg_elevated",
    "foreground": "text_primary",
    "border": "border_input",
    "background_surface": "bg_surface",
    "select_background": "select_bg",
    "select_foreground": "select_fg",
    "listbox_highlight": "border_input",
    # ключи PALETTE для кастомных tk-элементов
    "element_background": "bg_elevated",
    "element_foreground": "text_primary",
    "element_border": "border_input",
    "element_insertbackground": "text_primary",
    "element_selection_background": "select_bg",
    "element_selection_foreground": "select_fg",
    "element_inner_padding": (6, 3),
    "element_left_border_width": 3,
    "element_select_arrow_width": 8,
    "element_select_arrow_height": 5,
    "element_select_popup_borderwidth": 1,
    "element_select_popup_max_rows": 6,
    "element_select_popup_item_padding_left": 8,  # отступ слева у элементов в выпадающем списке
    "element_spin_arrow_size": (8, 4),  # (width, height) кнопок вверх/вниз у спинбокса
    "focuswidth": 0,
    "highlight_thickness": 0,
}

# Ключи клавиатуры для Ctrl+A/C/V/X (keycode -> действие); работают при любой раскладке.
# Windows: VK_A=65, VK_C=67, VK_V=86, VK_X=88; на X11 keycode = keysym (a=97, c=99, v=118, x=120).
INPUT_KEYCODES = {
    65: "select_all",
    97: "select_all",
    67: "copy",
    99: "copy",
    86: "paste",
    118: "paste",
    88: "cut",
    120: "cut",
}

# Разделитель: цвет, толщина линии, отступы (отдельно для горизонтального и вертикального)
UI_SEPARATOR = {
    "color": STL_COLOR_BORDER,
    "width_px": 1,
    "padding_horizontal_px": 12,  # отступы сверху и снизу у горизонтальной линии
    "padding_vertical_px": 8,    # отступы слева и справа у вертикальной линии
}

# Типографика: заголовки и подзаголовки. font_size — ключ UI_FONT_SIZE, padding, muted, pady_after
UI_TYPOGRAPHY = {
    "page_title": {"font_size": "extra_large", "padding": (0, 8), "muted": False, "pady_after": 8},
    "page_subtitle": {"font_size": "small", "padding": (0, 4), "muted": True, "pady_after": 4},
    "header_2": {"font_size": "large", "padding": (0, 6), "muted": False, "pady_after": 6},
    "header_3": {"font_size": "medium", "padding": (0, 4), "muted": False, "pady_after": 4},
    "header_3_light": {"font_size": "medium", "padding": (0, 4), "muted": True, "pady_after": 4},
}
UI_HEADERS = UI_TYPOGRAPHY  # алиас для совместимости

# Поля настроек: лейбл и описание — отдельные элементы; вёрстка в две колонки.
# label_font_size — размер подписи поля (ключ UI_FONT_SIZE).
# description_font_size — размер комментария под полем (текст под лейблом в табах настроек).
UI_INPUT_LABEL_DESCRIPTION = {
    "label_font_size": "small",
    "description_font_size": "extra_small",
    "description_muted": True,
    "pady_between": 0,
    "pady_after": 4,
    "column_label_width_px": 240,
    "column_field_width_px": 240,
}

# Блок настроек: все вертикальные зазоры одинаковые (gap_px). Отступы только отсюда.
GAP_PX = 8
UI_SETTINGS_BLOCK = {
    "container_width_px": 480,
    "column_label_px": 240,
    "column_field_px": 240,
    "gap_px": GAP_PX,
    "row_pady_top": 0,
    "row_pady_bottom": 0,
    "comment_pady_top": 0,
    "comment_pady_bottom": GAP_PX,
    "first_row_pady_top": GAP_PX,
    "intro_banner_pady_bottom": GAP_PX,
    "label_pady": 2,
    "field_padx": 5,
    "field_pady": 2,
    "block_sep_top": GAP_PX,
    "block_sep_bottom": 0,
}

# Модалки: отступы и размеры карточки, перенос текста
MODAL_CARD_WIDTH = 440
MODAL_CARD_MIN_HEIGHT = 0
MODAL_CARD_PADX = 16
MODAL_CARD_PADY_TOP = 8
MODAL_CARD_PADY_BOTTOM = 14
MODAL_MESSAGE_WRAP = 400
MODAL_FONT_HEADER = (FONT_FAMILY_UI, UI_FONT_SIZE["medium"])
MODAL_FONT_BODY = (FONT_FAMILY_UI, UI_FONT_SIZE["small"])


# Верхняя панель экрана: padding — отступы контейнера (горизонтальный, вертикальный), gap — зазор между кнопками
GUI_TOPBAR = {
    "padding": (12, 12),
    "gap": (8, 8),
    "background": STL_COLOR_BG_ELEVATED,
}

# Контейнер под верхней панелью: только padding и background (без gap)
GUI_CONTENT_WRAPPER = {
    "padding": (12, 12),
    "background": PALETTE["bg_surface"],
}

GUI_PADDING = {
    "layout": (0, 0),
}

# Visual rhythm
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
}

# Слот контента: отступ области экранов, блок «Обработка данных»
SCREEN_WRAPPER_PADDING = 16
PROCESSING_BLOCK_HEIGHT_PX = 220
PROCESSING_BLOCK_HEADER_PADX = 16

# Параметры скролл-области (ScrollableFrame): один источник истины
SCROLL_AREA = {
    "width": 8,
    "thumb": PALETTE["scrollbar_thumb"],
    "trough": PALETTE["scrollbar_trough"],
    "active": PALETTE["scrollbar_hover"],
    "arrow": PALETTE["text_muted"],
}


# Применение темы к root: template/styles/template.py (GUITemplate), обёртка gui_setup_theme в template/styles/__init__.py
