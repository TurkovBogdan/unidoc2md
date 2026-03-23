#!/usr/bin/env python3
"""Точка входа: инициализация и запуск приложения."""

from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

# Чтобы при запуске `python main.py` из корня проекта находился пакет src
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.app import app_root  # noqa: E402 — импорт выполняет boot


def _parse_cli_project(argv: list[str]) -> str | None:
    """Извлекает значение --project из argv. Возвращает None, если не задано."""
    for i, arg in enumerate(argv):
        if arg == "--project" and i + 1 < len(argv):
            return argv[i + 1].strip() or None
    return None


def _run_app() -> None:
    t0 = time.perf_counter()
    try:
        from src.core.logger import get_system_logger
        log = get_system_logger()
        if log:
            log.info("Старт готов за %.2f с", time.perf_counter() - t0)
    except Exception:
        pass

    if "--cli" in sys.argv:
        from src.app import main as cli_main  # noqa: E402
        project_name = _parse_cli_project(sys.argv)
        cli_main(project_name)
    else:
        from src.gui import main  # noqa: E402
        main(app_root)


def _fatal_error(message: str, is_gui: bool) -> None:
    if is_gui:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Ошибка", message)
            root.destroy()
        except Exception:
            print(message, file=sys.stderr)
    else:
        print(message, file=sys.stderr)
        if getattr(sys, "frozen", False):
            input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        _run_app()
    except KeyboardInterrupt:
        log = None
        try:
            from src.core.logger import get_system_logger
            log = get_system_logger()
        except Exception:
            pass
        if log:
            log.warning("Прервано пользователем (Ctrl+C)")
        else:
            print("Прервано пользователем (Ctrl+C)", file=sys.stderr)
        sys.exit(130)
    except SystemExit:
        raise
    except Exception:
        log = None
        try:
            from src.core.logger import get_system_logger
            log = get_system_logger()
        except Exception:
            pass
        if log:
            log.exception("Верхнеуровневая ошибка приложения")
        else:
            traceback.print_exc()
        _fatal_error(
            "Произошла ошибка. Подробности в логе (logs/system.log).",
            is_gui=("--cli" not in sys.argv),
        )
        sys.exit(1)
