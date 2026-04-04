"""Smoke: GUI bootstrap builds layout and all registered screens (no blocking mainloop)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path

import pytest

from src.core import AppConfigStore, set_language
from src.core.app_locale import AppLocaleStore, set_available_languages
from src.core.app_path import resolve_packaged_assets_data_path
from src.gui.adapters import llm_models as llm_models_adapter_mod
from src.gui.bootstrap import GUIBootstrap
from src.gui.gui_config import GUIConfigStore
from src.gui.gui_controller import GUIController
from src.modules.llm_models_registry.bootstrap import module_llm_model_registry_boot
from src.modules.llm_models_registry.module import ModuleConfigStore
from src.modules.llm_models_registry.providers.llm_model_store import reset_llm_model_store

_EXPECTED_SCREENS = frozenset(
    {
        "loading",
        "settings",
        "model_settings",
        "model_settings_detail",
        "project_list",
        "project_pipeline",
    }
)


@pytest.fixture(autouse=True)
def _app_config_and_locale(tmp_path: Path) -> None:
    """Minimal app.ini + catalogs so GUIBootstrap / locmsg work like in the app."""
    AppConfigStore.reset()
    AppConfigStore.load_or_create(tmp_path)
    set_available_languages(
        {
            "ru": "Русский",
            "en": "English",
            "zh": "中文",
        }
    )
    AppLocaleStore.reset()
    set_language("ru")


def test_gui_bootstrap_and_controller_build_all_screens(tmp_path: Path) -> None:
    """
    Full chain: fonts/theme → root → layout → every screen widget tree (incl. model detail).

    mainloop is replaced so the test exits; Tcl/Tk must accept the built widgets (regression
    for e.g. Label padding quirks on Windows).
    """
    GUIConfigStore.reset()
    GUIController._instance = None

    module_llm_model_registry_boot(
        resolve_packaged_assets_data_path("llm_models_registry.json"),
        tmp_path / "llm_models_registry.json",
    )

    root = GUIBootstrap.init(tmp_path)
    root.mainloop = lambda: None  # type: ignore[method-assign]

    try:
        GUIController.init(tmp_path, root)
        ctrl = GUIController.get()

        root.update_idletasks()
        assert root.winfo_exists()

        registry = ctrl._registry  # noqa: SLF001
        names = registry.names()
        assert _EXPECTED_SCREENS <= names, f"expected all core screens, got {names!r}"

        for code in _EXPECTED_SCREENS:
            frame = registry.get(code)
            assert frame is not None
            assert frame.winfo_exists()

        assert ctrl._gui_layout is not None  # noqa: SLF001
        assert ctrl._router is not None  # noqa: SLF001
    finally:
        GUIController._instance = None
        GUIConfigStore.reset()
        ModuleConfigStore.reset()
        reset_llm_model_store()
        llm_models_adapter_mod._adapters.clear()
        try:
            if root.winfo_exists():
                for child in list(root.winfo_children()):
                    child.destroy()
                root.withdraw()
        except tk.TclError:
            pass
