"""Startup preparation for the core application runtime."""

from .core_bootstrap import CoreBootstrap, core_boot, lang_boot

prepare_core_runtime = core_boot

__all__ = ["CoreBootstrap", "core_boot", "lang_boot", "prepare_core_runtime"]
