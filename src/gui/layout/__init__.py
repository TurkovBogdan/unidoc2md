"""
Layout package: application slot shell.

Public API for `GUILayout`:
  - ``build_loader_slot(parent) -> ttk.Frame``
  - ``build_content_slot(parent) -> ContentSlotResult``
  - ``build_content_console_slot(parent) -> ContentConsoleSlotResult``

Screen layout blocks (`SettingsBlock`, `grid_section_banner`, etc.) live under
``template/components``.
"""

from .content import build_content_console_slot, build_content_slot
from .loader import build_loader_slot

__all__ = [
    "build_content_slot",
    "build_content_console_slot",
    "build_loader_slot",
]
