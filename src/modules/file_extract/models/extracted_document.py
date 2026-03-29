"""Extract-stage models: content units and extraction result."""

from __future__ import annotations

from src.core.utils.hash import md5_string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from src.modules.file_discovery.models import DiscoveredDocument
from .extract_config import ExtractConfig
_UNSET = object()

# Carrier content type
CONTENT_TYPE_TEXT = "text"
CONTENT_TYPE_IMAGE = "image"
CONTENT_TYPE_MARKDOWN = "markdown"
ExtractedDocumentContentType = Literal[CONTENT_TYPE_TEXT, CONTENT_TYPE_IMAGE, CONTENT_TYPE_MARKDOWN]

# Semantic meaning (not the carrier format)
SEMANTIC_TYPE_MARKDOWN = "markdown"
SEMANTIC_TYPE_REQUIRED_DETECTION = "required_detection"
SEMANTIC_TYPE_DOCUMENT_FRAGMENT = "document_fragment"
SemanticType = Literal[
    SEMANTIC_TYPE_MARKDOWN,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
]


@dataclass
class ExtractedDocumentContent:
    """One extracted content unit: text or image with path to the cached file (path may be None after OCR)."""

    # Classification / processing
    content_type: ExtractedDocumentContentType
    semantic_type: SemanticType

    # Storage / format
    path: Path | str | None
    mime_type: str | None = None

    # Cache identity
    content_hash: str | None = None

    # Payload
    value: Any = None

    def path_obj(self) -> Path | None:
        if self.path is None:
            return None
        return self.path if isinstance(self.path, Path) else Path(self.path)

    def replace_content(
        self,
        *,
        content_type: ExtractedDocumentContentType | None = None,
        semantic_type: SemanticType | None = None,
        path: Path | str | None | object = _UNSET,
        mime_type: str | None = None,
        content_hash: str | None | object = _UNSET,
        value: Any | object = _UNSET,
    ) -> "ExtractedDocumentContent":
        """Return a new content unit with selected fields replaced."""
        next_mime = mime_type if mime_type is not None else self.mime_type
        return ExtractedDocumentContent(
            content_type=content_type if content_type is not None else self.content_type,
            semantic_type=semantic_type if semantic_type is not None else self.semantic_type,
            path=self.path if path is _UNSET else path,
            mime_type=next_mime,
            content_hash=self.content_hash if content_hash is _UNSET else content_hash,
            value=self.value if value is _UNSET else value,
        )


def compute_extract_hash(config: ExtractConfig, file_hash: str | None) -> str:
    """Cache key hash: canonical config + file hash."""
    canon = config.to_canonical_string()
    file_part = file_hash or ""
    combined = f"{canon}\nfile_hash={file_part}"
    return md5_string(combined)


@dataclass
class ExtractedDocument:
    """Extract result with source file metadata and a list of content units."""

    source: DiscoveredDocument
    config: ExtractConfig
    extract_hash: str
    content_hash: str | None = None
    content: list[ExtractedDocumentContent] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.content is None:
            object.__setattr__(self, "content", [])
