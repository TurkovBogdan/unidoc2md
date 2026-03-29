"""Markdown extract provider: save as-is, strip YAML front matter, or rebuild via LLM."""

from __future__ import annotations

import threading
from pathlib import Path

from src.modules.file_discovery.models import DiscoveredDocument
from ...interfaces import FileExtractProvider
from ...services.file_extract_cache import FileExtractCacheService
from ...models import (
    CONTENT_TYPE_MARKDOWN,
    CONTENT_TYPE_TEXT,
    ExtractConfig,
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_MARKDOWN,
    SourceDocument,
)
from src.modules.markdown.utils.yaml_frontmatter import clear_markdown_yaml
from src.modules.settings_schema.models import SettingFieldSchema


MARKDOWN_ALGORITHM_SKIP = "skip"
MARKDOWN_LOGIC_SAVE_AS_IS = "save_as_is"
MARKDOWN_LOGIC_SAVE_CLEAR_TAGS = "save_clear_tags"
MARKDOWN_LOGIC_REBUILD_LLM = "rebuild_llm"


class MarkdownExtractProvider(FileExtractProvider):
    """Extract .md as one content block (markdown or text) per selected algorithm."""

    PROVIDER_CODE: str = "markdown_extract_provider"

    @staticmethod
    def supported_extensions() -> set[str]:
        return {".md"}

    @classmethod
    def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
        return (
            SettingFieldSchema(
                key="algorithm",
                type="select",
                default=MARKDOWN_LOGIC_SAVE_CLEAR_TAGS,
                label="algorithm",
                description="",
                options=(
                    (MARKDOWN_ALGORITHM_SKIP, MARKDOWN_ALGORITHM_SKIP),
                    (MARKDOWN_LOGIC_SAVE_AS_IS, MARKDOWN_LOGIC_SAVE_AS_IS),
                    (MARKDOWN_LOGIC_SAVE_CLEAR_TAGS, MARKDOWN_LOGIC_SAVE_CLEAR_TAGS),
                    (MARKDOWN_LOGIC_REBUILD_LLM, MARKDOWN_LOGIC_REBUILD_LLM),
                ),
            ),
        )

    @staticmethod
    def _build_discovered_document(source: SourceDocument) -> DiscoveredDocument:
        return DiscoveredDocument(
            path=str(source.path),
            folder=source.folder,
            filename=source.filename,
            extension=source.normalized_extension(),
            mime_type=source.mime_type,
            hash=source.file_hash,
        )

    def extract(
        self,
        source: SourceDocument,
        config: ExtractConfig,
        storage: FileExtractCacheService,
        document_hash: str,
        cancel_event: threading.Event | None = None,
    ) -> ExtractedDocument:
        if cancel_event is not None and cancel_event.is_set():
            return ExtractedDocument(
                source=self._build_discovered_document(source),
                config=config,
                extract_hash=document_hash,
                content=[],
            )
        logic = (self.get_setting(config, "algorithm") or MARKDOWN_LOGIC_SAVE_CLEAR_TAGS).strip().lower()
        if logic == MARKDOWN_ALGORITHM_SKIP:
            return ExtractedDocument(
                source=self._build_discovered_document(source),
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

        if logic == MARKDOWN_LOGIC_SAVE_AS_IS:
            pass
        elif logic == MARKDOWN_LOGIC_SAVE_CLEAR_TAGS:
            text = clear_markdown_yaml(text)
        elif logic == MARKDOWN_LOGIC_REBUILD_LLM:
            text = clear_markdown_yaml(text)

        content: list[ExtractedDocumentContent] = []
        if logic == MARKDOWN_LOGIC_SAVE_AS_IS or logic == MARKDOWN_LOGIC_SAVE_CLEAR_TAGS:
            content_type = CONTENT_TYPE_MARKDOWN
            semantic_type = SEMANTIC_TYPE_MARKDOWN
            ext = ".md"
        else:
            assert logic == MARKDOWN_LOGIC_REBUILD_LLM
            content_type = CONTENT_TYPE_TEXT
            semantic_type = SEMANTIC_TYPE_DOCUMENT_FRAGMENT
            ext = ".txt"

        item = storage.save_text_content(
            text, f"{stem}{ext}", content_type=content_type, semantic_type=semantic_type
        )
        if item is not None:
            content.append(item)
        return ExtractedDocument(
            source=self._build_discovered_document(source),
            config=config,
            extract_hash=document_hash,
            content=content,
        )
