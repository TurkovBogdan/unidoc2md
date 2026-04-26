"""Public API smoke tests for file_discovery."""

from __future__ import annotations


def test_import_module_standalone() -> None:
    """Module public API imports without depending on the rest of the app."""
    from src.modules.file_discovery import (
        DiscoveryConfig,
        DiscoveredDocument,
        DiscoveryService,
        FileDiscoveryAccessDeniedError,
        FileDiscoveryError,
        FileDiscoveryHashIOError,
        FileDiscoveryPathNotFoundError,
        HashSidecarService,
        SKIP_EXTENSIONS,
    )

    assert DiscoveryConfig is not None
    assert DiscoveredDocument is not None
    assert DiscoveryService is not None
    assert HashSidecarService is not None
    assert issubclass(FileDiscoveryPathNotFoundError, FileDiscoveryError)
    assert issubclass(FileDiscoveryAccessDeniedError, FileDiscoveryError)
    assert issubclass(FileDiscoveryHashIOError, FileDiscoveryError)
    assert ".md5" in SKIP_EXTENSIONS
