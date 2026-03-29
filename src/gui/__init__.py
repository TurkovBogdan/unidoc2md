"""unidoc2md project GUI configurator.

Window entry point: ``src.app.main_gui`` (not re-exported here so the ``gui`` package
does not depend on ``app`` or risk import cycles).
"""

from .bootstrap import GUIBootstrap

__all__ = ["GUIBootstrap"]
