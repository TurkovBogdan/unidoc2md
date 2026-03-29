"""Base document extract provider: supported_extensions and extract."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ..models import ExtractedDocument
from src.modules.settings_schema.models import SettingFieldSchema

if TYPE_CHECKING:
    from ..services.file_extract_cache import FileExtractCacheService
    from ..models import ExtractConfig, SourceDocument


class FileExtractProvider(ABC):
    """Base class for extracting document content into cache-backed artifacts."""

    PROVIDER_CODE: str = ""
    PROVIDER_TITLE: str = ""
    PROVIDER_DESCRIPTION: str = ""

    @classmethod
    def provider_code(cls) -> str:
        """Provider id (snake_case). Taken from PROVIDER_CODE on the concrete class."""
        return cls.PROVIDER_CODE

    @classmethod
    def provider_title(cls) -> str:
        """Provider id used for GUI localization (project_extract.provider.<code>.title)."""
        return cls.PROVIDER_CODE

    @classmethod
    def provider_description(cls) -> str:
        """Group description for UI; empty means labels only on schema fields."""
        return cls.PROVIDER_DESCRIPTION

    def get_setting(self, config: "ExtractConfig", key: str, default: Any = None) -> Any:
        """Return a provider setting by schema key (provider_code implied)."""
        return config.get_provider_value(type(self).provider_code(), key, default)

    @staticmethod
    @abstractmethod
    def supported_extensions() -> set[str]:
        """Set of supported extensions (lowercase, with a leading dot)."""
        ...

    @classmethod
    @abstractmethod
    def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
        """Field schema: label = key (code), description empty; select uses (value code, option code). GUI localizes."""
        ...

    @abstractmethod
    def extract(
        self,
        source: "SourceDocument",
        config: "ExtractConfig",
        storage: "FileExtractCacheService",
        document_hash: str,
        cancel_event: threading.Event | None = None,
    ) -> ExtractedDocument:
        """Extract document content; persist artifacts via storage when needed."""
        ...
