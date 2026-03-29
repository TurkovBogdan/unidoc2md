"""
ttk styling: theme, colors, spacing. Apply to root via gui_setup_theme(root) in template/styles.

Rule: ALL style parameters (colors, sizes, padding, fonts, etc.) live only in this file —
src/gui/template/styles/theme.py. Do not hardcode numbers/colors in components, elements, or
screens; use PALETTE, UI_*, and constants from this module.
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Base colors — prefix STL_COLOR_<role>. PALETTE / STL_COLORS below.
# -----------------------------------------------------------------------------

# Background
STL_COLOR_BG = "#0f1410"
STL_COLOR_BG_SURFACE = "#1a2218"
STL_COLOR_BG_ELEVATED = "#293628"
STL_COLOR_MODAL_OVERLAY = "#080808"

# Text
STL_COLOR_TEXT_PRIMARY = "#d8e4d6"
STL_COLOR_TEXT_SOFT = "#a8b8a4"  # between primary and muted, slightly subdued
STL_COLOR_TEXT_MUTED = "#7a8f76"

# Selection (background and foreground)
STL_COLOR_SELECT_BACKGROUND = "#2d4a2d"
STL_COLOR_SELECT_TEXT = "#e0ece0"

# Border
STL_COLOR_BORDER = "#2d352d"
STL_COLOR_BORDER_INPUT = "#3a4b39"

# Scrollbar: trough slightly lighter than bg_surface, thumb matches panels (bg_elevated)
STL_COLOR_SCROLL_TROUGH = "#1e261c"
STL_COLOR_SCROLL_THUMB = STL_COLOR_BG_ELEVATED
STL_COLOR_SCROLL_HOVER = "#334332"

# -----------------------------------------------------------------------------
# UI elements (buttons): PRIMARY, SECONDARY, GHOST, DISABLED.
# Each group: base, hover, pressed, text color.
# -----------------------------------------------------------------------------

# PRIMARY — main action
UI_COLOR_PRIMARY = "#457045"
UI_COLOR_PRIMARY_HOVER = "#5d9a5d"  # brighter on hover
UI_COLOR_PRIMARY_PRESSED = "#345834"
UI_COLOR_PRIMARY_TEXT = "#d8e4d6"

# SECONDARY — secondary action (lighter than bg, slightly darker than Primary)
UI_COLOR_SECONDARY = "#364a36"
UI_COLOR_SECONDARY_HOVER = "#4a634a"  # brighter on hover
UI_COLOR_SECONDARY_PRESSED = "#2d3d2d"
UI_COLOR_SECONDARY_TEXT = "#d8e4d6"

# GHOST — low-emphasis action (Secondary-like tone, shifted toward gray)
UI_COLOR_GHOST = "#242624"
UI_COLOR_GHOST_HOVER = "#2a2c2a"
UI_COLOR_GHOST_PRESSED = "#1e201e"
UI_COLOR_GHOST_TEXT = "#d8e4d6"

# DISABLED
UI_COLOR_DISABLED = "#232d20"
UI_COLOR_DISABLED_HOVER = "#232d20"
UI_COLOR_DISABLED_PRESSED = "#232d20"
UI_COLOR_DISABLED_TEXT = "#7a8f76"

# Tabs: colors (like Primary/Secondary buttons), label and content padding.
# content_padding — (padx, pady) for tab content container: top/bottom only, no left/right.
UI_TABS = {
    "active": UI_COLOR_PRIMARY,
    "inactive": UI_COLOR_SECONDARY,
    "hover": UI_COLOR_PRIMARY_HOVER,
    "pressed": UI_COLOR_PRIMARY_PRESSED,
    "inactive_hover": UI_COLOR_SECONDARY_HOVER,
    "inactive_pressed": UI_COLOR_SECONDARY_PRESSED,
    "underline": STL_COLOR_BORDER,  # line under tab bar
    "gap_px": 8,
    "bar_padding_y": 2,
    "margin_after_line_px": 8,
    "item_padx": 10,  # same as UI_BUTTONS["padding"][0]
    "item_pady": 6,  # same as UI_BUTTONS["padding"][1]
    "underline_height_px": 1,
    "content_padding": (0, 12),  # (padx, pady): top/bottom only
    "content_first_row_pady_top": 8,  # top padding before first content row (all tabs)
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

# Fonts: set in gui_setup_theme (template.styles) from bootstrap or fallback; one face for UI and mono.
FONT_FAMILY_UI = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

# Font sizes in points. In font=() use UI_FONT_SIZE["key"], do not hardcode numbers.
UI_FONT_SIZE = {
    "extra_small": 9,
    "small": 10,
    "medium": 12,
    "large": 14,
    "extra_large": 16,
}


# Buttons: padding, no border, no visible focus ring.
# font_size — UI_FONT_SIZE key for button text.
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

# Inputs: ttk and custom tk widgets. Single source of truth for all project inputs.
# font_size — UI_FONT_SIZE key for Entry, Spinbox, Combobox, etc.
UI_INPUTS = {
    "font_size": "small",
    "borderwidth": 1,
    "relief": "flat",
    "entry_layout_border": "1",  # border thickness in TEntry layout
    "padding": (4, 2),  # inner padding for Combobox / Spinbox
    "entry_padding": (0, 0),  # TEntry: remove inner pseudo-border around text
    # PALETTE keys for standard ttk widgets
    "field_background": "bg_elevated",
    "foreground": "text_primary",
    "border": "border_input",
    "background_surface": "bg_surface",
    "select_background": "select_bg",
    "select_foreground": "select_fg",
    "listbox_highlight": "border_input",
    # PALETTE keys for custom tk widgets
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
    "element_select_popup_item_padding_left": 8,  # left padding for dropdown items
    "element_spin_arrow_size": (8, 4),  # (width, height) for spin up/down
    "focuswidth": 0,
    "highlight_thickness": 0,
}

# Keycodes for Ctrl+A/C/V/X (keycode -> action); work with any keyboard layout.
# Windows: VK_A=65, VK_C=67, VK_V=86, VK_X=88; X11 keycode = keysym (a=97, c=99, v=118, x=120).
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

# Separator: color, line width, padding (horizontal vs vertical)
UI_SEPARATOR = {
    "color": STL_COLOR_BORDER,
    "width_px": 1,
    "padding_horizontal_px": 12,  # top/bottom around horizontal line
    "padding_vertical_px": 8,  # left/right around vertical line
}

# Typography: titles and subtitles. font_size — UI_FONT_SIZE key; padding, muted, pady_after
UI_TYPOGRAPHY = {
    "page_title": {"font_size": "extra_large", "padding": (0, 8), "muted": False, "pady_after": 8},
    "page_subtitle": {"font_size": "small", "padding": (0, 4), "muted": True, "pady_after": 4},
    "header_2": {"font_size": "large", "padding": (0, 6), "muted": False, "pady_after": 6},
    "header_3": {"font_size": "medium", "padding": (0, 4), "muted": False, "pady_after": 4},
    "header_3_light": {"font_size": "medium", "padding": (0, 4), "muted": True, "pady_after": 4},
}
UI_HEADERS = UI_TYPOGRAPHY  # backward-compat alias

# Settings fields: label and description as separate widgets; two-column layout.
# label_font_size — field label size (UI_FONT_SIZE key).
# description_font_size — hint under field (settings tabs).
UI_INPUT_LABEL_DESCRIPTION = {
    "label_font_size": "small",
    "description_font_size": "extra_small",
    "description_muted": True,
    "pady_between": 0,
    "pady_after": 4,
    "column_label_width_px": 240,
    "column_field_width_px": 240,
}

# Settings block: uniform vertical gaps (gap_px). Spacing values come only from here.
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

# Modals: card padding/size, text wrap
MODAL_CARD_WIDTH = 440
MODAL_CARD_MIN_HEIGHT = 0
MODAL_CARD_PADX = 16
MODAL_CARD_PADY_TOP = 8
MODAL_CARD_PADY_BOTTOM = 14
MODAL_MESSAGE_WRAP = 400
MODAL_FONT_HEADER = (FONT_FAMILY_UI, UI_FONT_SIZE["medium"])
MODAL_FONT_BODY = (FONT_FAMILY_UI, UI_FONT_SIZE["small"])


# Screen top bar: padding — container (horizontal, vertical), gap — between buttons
GUI_TOPBAR = {
    "padding": (12, 12),
    "gap": (8, 8),
    "background": STL_COLOR_BG_ELEVATED,
}

# Content under top bar: padding and background only (no gap)
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

# Content slot: screen area padding, data processing block
SCREEN_WRAPPER_PADDING = 16
PROCESSING_BLOCK_HEIGHT_PX = 220
PROCESSING_BLOCK_HEADER_PADX = 16

# ScrollableFrame scrollbar: single source of truth
SCROLL_AREA = {
    "width": 8,
    "thumb": PALETTE["scrollbar_thumb"],
    "trough": PALETTE["scrollbar_trough"],
    "active": PALETTE["scrollbar_hover"],
    "arrow": PALETTE["text_muted"],
}


# Theme application: template/styles/template.py (GUITemplate), gui_setup_theme in template/styles/__init__.py
