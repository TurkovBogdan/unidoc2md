"""Plain-text extract provider: read file body into cache as text."""

from __future__ import annotations

from pathlib import Path

from src.modules.file_discovery.models import DiscoveredDocument
from ...interfaces import FileExtractProvider
from ...services.file_extract_cache import FileExtractCacheService
from ...models import (
    CONTENT_TYPE_TEXT,
    ExtractConfig,
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SourceDocument,
)
from src.modules.settings_schema.models import SettingFieldSchema


TEXT_ALGORITHM_SKIP = "skip"
TEXT_ALGORITHM_ONLY_TEXT = "only_text"


class TextExtractProvider(FileExtractProvider):
    """Extract text formats: read file and store contents in cache."""

    PROVIDER_CODE: str = "text_extract_provider"

    @staticmethod
    def supported_extensions() -> set[str]:
        return {".txt"}

    @classmethod
    def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
        return (
            SettingFieldSchema(
                key="algorithm",
                type="select",
                default=TEXT_ALGORITHM_ONLY_TEXT,
                label="algorithm",
                description="",
                options=(
                    (TEXT_ALGORITHM_SKIP, TEXT_ALGORITHM_SKIP),
                    (TEXT_ALGORITHM_ONLY_TEXT, TEXT_ALGORITHM_ONLY_TEXT),
                ),
            ),
        )

    def extract(
        self,
        source: SourceDocument,
        config: ExtractConfig,
        storage: FileExtractCacheService,
        document_hash: str,
    ) -> ExtractedDocument:
        algorithm = (self.get_setting(config, "algorithm") or TEXT_ALGORITHM_ONLY_TEXT).strip().lower()
        if algorithm == TEXT_ALGORITHM_SKIP:
            return ExtractedDocument(
                source=DiscoveredDocument(
                    path=str(source.path),
                    folder=source.folder,
                    filename=source.filename,
                    extension=source.normalized_extension(),
                    mime_type=source.mime_type,
                    hash=source.file_hash,
                ),
                config=config,
                extract_hash=document_hash,
                content=[],
            )
        path = source.path_obj()
        stem = Path(source.filename).stem or "content"
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        ext = source.normalized_extension() or ".txt"
        content: list[ExtractedDocumentContent] = []
        item = storage.save_text_content(
            text,
            f"{stem}{ext}",
            content_type=CONTENT_TYPE_TEXT,
            semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
        )
        if item is not None:
            content.append(item)
        return ExtractedDocument(
            source=DiscoveredDocument(
                path=str(source.path),
                folder=source.folder,
                filename=source.filename,
                extension=source.normalized_extension(),
                mime_type=source.mime_type,
                hash=source.file_hash,
            ),
            config=config,
            extract_hash=document_hash,
            content=content,
        )
