"""Image extract provider: write standalone image files into cache as JPEG."""

from __future__ import annotations

from pathlib import Path

from src.modules.file_discovery.models import DiscoveredDocument
from ...interfaces import FileExtractProvider
from ...services.file_extract_cache import FileExtractCacheService
from ...services.image_processing_service import write_jpg_from_file
from ...models import (
    CONTENT_TYPE_IMAGE,
    ExtractConfig,
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
    SourceDocument,
)
from src.modules.settings_schema.models import SettingFieldSchema


IMAGE_ALGORITHM_SKIP = "skip"
IMAGE_ALGORITHM_VISION_OCR = "vision_ocr"


class ImageExtractProvider(FileExtractProvider):
    """Standalone images: convert to JPG; optional long-edge limit like other extract paths."""

    PROVIDER_CODE: str = "image_extract_provider"

    PAGE_IMAGE_FORMAT: str = "jpg"
    DEFAULT_MAX_SIZE: int = 1440

    @staticmethod
    def supported_extensions() -> set[str]:
        return {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".svg"}

    @classmethod
    def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
        return (
            SettingFieldSchema(
                key="algorithm",
                type="select",
                default=IMAGE_ALGORITHM_VISION_OCR,
                label="algorithm",
                description="",
                options=(
                    (IMAGE_ALGORITHM_SKIP, IMAGE_ALGORITHM_SKIP),
                    (IMAGE_ALGORITHM_VISION_OCR, IMAGE_ALGORITHM_VISION_OCR),
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

    def _normalize_max_size(self, config: ExtractConfig) -> int:
        raw = self.get_setting(config, "max_size", self.DEFAULT_MAX_SIZE)
        try:
            n = int(raw)
        except (TypeError, ValueError):
            n = self.DEFAULT_MAX_SIZE
        return max(1, n)

    def extract(
        self,
        source: SourceDocument,
        config: ExtractConfig,
        storage: FileExtractCacheService,
        document_hash: str,
    ) -> ExtractedDocument:
        algorithm = (self.get_setting(config, "algorithm") or IMAGE_ALGORITHM_VISION_OCR).strip().lower()
        if algorithm == IMAGE_ALGORITHM_SKIP:
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
        content: list[ExtractedDocumentContent] = []
        stem = Path(source.filename).stem or "image"
        source_path = source.path_obj()
        max_size = self._normalize_max_size(config)

        def _write_converted(path: Path) -> None:
            write_jpg_from_file(
                source_path,
                path,
                source_ext=source.normalized_extension(),
                max_long_edge=max_size,
            )

        item = storage.save_generated_file_content(
            filename=f"{stem}.jpg",
            writer=_write_converted,
            content_type=CONTENT_TYPE_IMAGE,
            semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
        )
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
