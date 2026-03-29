"""Main service: extension → provider map, get_supported_extensions(), extract()."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from src.modules.file_discovery.models import DiscoveredDocument
from .file_extract_cache import FileExtractCacheService
from ..providers.file_extract_provider import (
    get_extension_map,
    get_supported_extensions as _registry_supported_extensions,
)
from ..models import (
    ExtractedDocument,
    ExtractConfig,
    SourceDocument,
    compute_extract_hash,
)

if TYPE_CHECKING:
    from src.core.logger import SystemLogger


class FileExtractService:
    """Content extraction with hash-based cache, provider selection by extension, extract with config and storage."""

    def __init__(self, logger: SystemLogger | None = None) -> None:
        self._extension_map = get_extension_map()
        self._logger = logger

    @staticmethod
    def get_supported_extensions() -> set[str]:
        """Union of extensions from all registered providers."""
        return _registry_supported_extensions()

    def extract(
        self,
        config: ExtractConfig,
        source: SourceDocument,
        cancel_event: threading.Event | None = None,
    ) -> ExtractedDocument | None:
        """
        Compute hash (config + file); return cached ExtractedDocument if present.
        Otherwise pick provider by extension. If unsupported or disabled, return None.
        Otherwise build FileExtractCacheService(config, extract_hash), call provider.extract(...),
        save to cache, return result.
        """
        if cancel_event is not None and cancel_event.is_set():
            return None
        doc_hash = compute_extract_hash(config, source.file_hash)
        cached = FileExtractCacheService.load_extracted_document(config, doc_hash)
        if cached is not None:
            # Cache holds extract payload and file_hash only; source metadata always comes from the current document.
            return ExtractedDocument(
                source=DiscoveredDocument(
                    path=str(source.path),
                    folder=source.folder,
                    filename=source.filename,
                    extension=source.normalized_extension(),
                    mime_type=source.mime_type,
                    hash=source.file_hash or cached.source.hash,
                ),
                config=cached.config,
                extract_hash=cached.extract_hash,
                content_hash=cached.content_hash,
                content=cached.content,
            )
        ext = source.normalized_extension()
        provider = self._extension_map.get(ext)
        if provider is None:
            if self._logger is not None:
                self._logger.warning(
                    "file_extract.skip_no_provider extension=%s path=%s",
                    ext,
                    source.path,
                )
            return None
        if cancel_event is not None and cancel_event.is_set():
            return None
        storage = FileExtractCacheService(config, doc_hash)
        doc = provider.extract(
            source,
            config,
            storage,
            document_hash=doc_hash,
            cancel_event=cancel_event,
        )
        if cancel_event is not None and cancel_event.is_set():
            return None
        storage.save_extracted_document(doc)
        return doc
