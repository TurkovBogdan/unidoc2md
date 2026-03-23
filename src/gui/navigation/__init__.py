"""Маршрутизация и registry экранов: переходы, lifecycle."""

from .router import GUIRouter
from .screen_registry import ScreenRegistry

__all__ = ["GUIRouter", "ScreenRegistry"]