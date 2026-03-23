"""Точка входа GUI: main(app_root), делегирует в GUIController."""

from __future__ import annotations

from pathlib import Path

from src.core.logger import SYSTEM_LOGGER

from src.gui.bootstrap import GUIBootstrap
from src.gui.gui_controller import GUIController


def main(app_root: Path) -> None:
    """Запускает GUI-конфигуратор. app_root — корень приложения (Path). GUIBootstrap.init создаёт оформленный root, GUIController.init() — mainloop."""
    try:
        root = GUIBootstrap.init(app_root)
        GUIController.init(app_root, root)
    except Exception:
        SYSTEM_LOGGER.exception("Критическая ошибка при запуске GUI")
        raise
