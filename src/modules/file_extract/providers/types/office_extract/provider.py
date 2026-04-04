"""Office provider orchestrator for DOCX/ODT."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import BadZipFile

from src.modules.file_discovery.models import DiscoveredDocument
from ....interfaces import FileExtractProvider
from ....models import (
    CONTENT_TYPE_TEXT,
    ExtractConfig,
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
    SourceDocument,
)
from ....services.file_extract_cache import FileExtractCacheService
from .docx_extract import extract_docx
from .image_pipeline import OfficeImagePipeline
from .odt_extract import extract_odt
from src.modules.settings_schema.models import SettingFieldSchema


class OfficeExtractProvider(FileExtractProvider):
    """Extract content from office text formats preserving text/image order."""

    PROVIDER_CODE: str = "office_extract_provider"
    PAGE_IMAGE_FORMAT: str = "jpg"
    DEFAULT_MAX_SIZE: int = 1440
    ADAPTIVE_IMAGE_SIZE_SUM_THRESHOLD_PX: int = 560

    OFFICE_ALGORITHM_SKIP: str = "skip"
    OFFICE_ALGORITHM_ONLY_TEXT: str = "only_text"
    OFFICE_ALGORITHM_VISION_ALL: str = "vision_all"
    OFFICE_ALGORITHM_ADAPTIVE: str = "adaptive"
    OFFICE_ALGORITHMS: tuple[str, ...] = (
        OFFICE_ALGORITHM_SKIP,
        OFFICE_ALGORITHM_ONLY_TEXT,
        OFFICE_ALGORITHM_VISION_ALL,
        OFFICE_ALGORITHM_ADAPTIVE,
    )
    DEFAULT_OFFICE_ALGORITHM: str = OFFICE_ALGORITHM_ADAPTIVE
    OFFICE_EFFECTIVELY_NO_IMAGES_SUM_PX: int = 10**9

    @staticmethod
    def supported_extensions() -> set[str]:
        return {".docx", ".odt"}

    @classmethod
    def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
        return (
            SettingFieldSchema(
                key="algorithm",
                type="select",
                default=cls.DEFAULT_OFFICE_ALGORITHM,
                label="algorithm",
                description="",
                options=(
                    (cls.OFFICE_ALGORITHM_SKIP, cls.OFFICE_ALGORITHM_SKIP),
                    (cls.OFFICE_ALGORITHM_ONLY_TEXT, cls.OFFICE_ALGORITHM_ONLY_TEXT),
                    (cls.OFFICE_ALGORITHM_VISION_ALL, cls.OFFICE_ALGORITHM_VISION_ALL),
                    (cls.OFFICE_ALGORITHM_ADAPTIVE, cls.OFFICE_ALGORITHM_ADAPTIVE),
                ),
            ),
            SettingFieldSchema(
                key="max_size",
                type="int",
                default=cls.DEFAULT_MAX_SIZE,
                label="max_size",
                description="",
            ),
        )

    def extract(
        self,
        source: SourceDocument,
        config: ExtractConfig,
        storage: FileExtractCacheService,
        document_hash: str,
    ) -> ExtractedDocument:
        content: list[ExtractedDocumentContent] = []
        algorithm = (
            config.get_provider_value(self.PROVIDER_CODE, "algorithm", self.DEFAULT_OFFICE_ALGORITHM) or ""
        ).strip().lower()
        if algorithm == self.OFFICE_ALGORITHM_SKIP:
            return self._build_document(source, config, document_hash, content)

        path = source.path_obj()
        ext = source.normalized_extension()
        stem = Path(source.filename).stem or "document"
        if self._is_temporary_lock_file(path):
            return self._build_document(source, config, document_hash, content)

        if algorithm == self.OFFICE_ALGORITHM_ONLY_TEXT:
            min_px = self.OFFICE_EFFECTIVELY_NO_IMAGES_SUM_PX
        elif algorithm == self.OFFICE_ALGORITHM_VISION_ALL:
            min_px = None
        elif algorithm == self.OFFICE_ALGORITHM_ADAPTIVE:
            min_px = self.ADAPTIVE_IMAGE_SIZE_SUM_THRESHOLD_PX
        else:
            min_px = self.ADAPTIVE_IMAGE_SIZE_SUM_THRESHOLD_PX

        max_size = self._normalize_image_params(config)
        image_semantic = SEMANTIC_TYPE_REQUIRED_DETECTION
        pipeline = OfficeImagePipeline(
            storage=storage,
            stem=stem,
            convert_to=self.PAGE_IMAGE_FORMAT,
            max_size=max_size,
            image_semantic_type=image_semantic,
            min_size_sum_px=min_px,
        )

        if ext == ".docx":
            try:
                extract_docx(
                    path=path,
                    storage=storage,
                    pipeline=pipeline,
                    out=content,
                    flush_text=self._flush_text,
                )
            except (BadZipFile, KeyError, ET.ParseError, OSError, ValueError):
                pass
        elif ext == ".odt":
            try:
                extract_odt(
                    path=path,
                    storage=storage,
                    pipeline=pipeline,
                    out=content,
                    flush_text=self._flush_text,
                )
            except (BadZipFile, KeyError, ET.ParseError, OSError, ValueError):
                pass

        return self._build_document(source, config, document_hash, content)

    @staticmethod
    def _build_document(
        source: SourceDocument,
        config: ExtractConfig,
        document_hash: str,
        content: list[ExtractedDocumentContent],
    ) -> ExtractedDocument:
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

    @staticmethod
    def _is_temporary_lock_file(path: Path) -> bool:
        return path.name.lower().startswith("~$")

    @staticmethod
    def _normalize_image_params(config: ExtractConfig) -> int:
        raw = config.get_provider_value(OfficeExtractProvider.PROVIDER_CODE, "max_size", OfficeExtractProvider.DEFAULT_MAX_SIZE)
        try:
            max_size = int(raw)
        except (TypeError, ValueError):
            max_size = OfficeExtractProvider.DEFAULT_MAX_SIZE
        return max(1, max_size)

    @staticmethod
    def _flush_text(
        text_buffer: list[str],
        stem: str,
        text_index: int,
        storage: FileExtractCacheService,
        out: list[ExtractedDocumentContent],
    ) -> int:
        if not text_buffer:
            return text_index
        text = "".join(text_buffer)
        text_buffer.clear()
        text_index += 1
        item = storage.save_text_content(
            text,
            filename=f"{stem}_part{text_index}.txt",
            content_type=CONTENT_TYPE_TEXT,
            semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
        )
        if item is not None:
            out.append(item)
        return text_index
