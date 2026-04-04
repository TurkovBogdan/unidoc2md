"""PDF provider: text/image extraction with OCR-quality fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.modules.file_discovery.models import DiscoveredDocument
from src.modules.settings_schema.models import SettingFieldSchema
from ....interfaces import FileExtractProvider
from ....models import (
    CONTENT_TYPE_IMAGE,
    CONTENT_TYPE_TEXT,
    ExtractConfig,
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
    SourceDocument,
)
from ....services.file_extract_cache import FileExtractCacheService
from ....services.image_processing_service import write_rgb_to_path
from .text_quality import is_low_quality_ocr_text


class PdfExtractProvider(FileExtractProvider):
    """Extract content from PDF: text and/or pages as images."""

    PROVIDER_CODE: str = "pdf_extract_provider"

    PDF_ALGORITHM_SKIP: str = "skip"
    PDF_EXTRACT_MODE_IMAGES_ALWAYS: str = "images_always"
    PDF_EXTRACT_MODE_ONLY_TEXT: str = "only_text"
    PDF_EXTRACT_MODE_ADAPTIVE: str = "adaptive"
    PDF_ALGORITHMS: tuple[str, ...] = (
        PDF_ALGORITHM_SKIP,
        PDF_EXTRACT_MODE_ONLY_TEXT,
        PDF_EXTRACT_MODE_IMAGES_ALWAYS,
        PDF_EXTRACT_MODE_ADAPTIVE,
    )
    PDF_EXTRACT_MODES: tuple[str, ...] = (
        PDF_EXTRACT_MODE_ADAPTIVE,
        PDF_EXTRACT_MODE_IMAGES_ALWAYS,
        PDF_EXTRACT_MODE_ONLY_TEXT,
    )
    DEFAULT_PDF_ALGORITHM: str = PDF_EXTRACT_MODE_ADAPTIVE
    ADAPTIVE_IMAGE_SIZE_SUM_THRESHOLD_PX: int = 560

    PAGE_IMAGE_EXT: str = ".jpg"
    PAGE_IMAGE_FORMAT: str = "jpg"
    DEFAULT_PAGE_RENDER_MATRIX_SCALE: int = 2

    @staticmethod
    def supported_extensions() -> set[str]:
        return {".pdf"}

    @classmethod
    def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
        return (
            SettingFieldSchema(
                key="algorithm",
                type="select",
                default=cls.DEFAULT_PDF_ALGORITHM,
                label="algorithm",
                description="",
                options=(
                    (cls.PDF_ALGORITHM_SKIP, cls.PDF_ALGORITHM_SKIP),
                    (cls.PDF_EXTRACT_MODE_ONLY_TEXT, cls.PDF_EXTRACT_MODE_ONLY_TEXT),
                    (cls.PDF_EXTRACT_MODE_IMAGES_ALWAYS, cls.PDF_EXTRACT_MODE_IMAGES_ALWAYS),
                    (cls.PDF_EXTRACT_MODE_ADAPTIVE, cls.PDF_EXTRACT_MODE_ADAPTIVE),
                ),
            ),
            SettingFieldSchema(
                key="render_scale",
                type="select",
                default="2",
                label="render_scale",
                description="",
                options=(
                    ("1", "1"),
                    ("2", "2"),
                    ("3", "3"),
                    ("4", "4"),
                    ("5", "5"),
                ),
            ),
        )

    def _normalize_extract_params(self, config: ExtractConfig) -> tuple[str, int]:
        mode = (self.get_setting(config, "algorithm", self.DEFAULT_PDF_ALGORITHM) or "").strip()
        if mode not in self.PDF_EXTRACT_MODES:
            mode = self.DEFAULT_PDF_ALGORITHM

        raw_scale = self.get_setting(config, "render_scale", "2")
        try:
            scale = max(1, min(5, int(raw_scale)))
        except (TypeError, ValueError):
            scale = self.DEFAULT_PAGE_RENDER_MATRIX_SCALE

        return mode, scale

    @staticmethod
    def _get_page_text(page: Any) -> str:
        import fitz

        return page.get_text("text", clip=fitz.INFINITE_RECT(), sort=True) or ""

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

    @staticmethod
    def _page_has_images(page: Any) -> bool:
        return bool(page.get_images(full=True))

    @staticmethod
    def _page_has_large_image(page: Any, threshold_sum_px: int) -> bool:
        images = page.get_images(full=True)
        for image in images:
            if len(image) < 4:
                continue
            width = image[2]
            height = image[3]
            if isinstance(width, int) and isinstance(height, int) and (width + height) >= threshold_sum_px:
                return True
        return False

    def _extract_only_text(
        self,
        pdf: Any,
        storage: FileExtractCacheService,
        stem: str,
    ) -> list[ExtractedDocumentContent]:
        content: list[ExtractedDocumentContent] = []
        for index, page in enumerate(pdf):
            item = storage.save_text_content(
                self._get_page_text(page),
                f"{stem}_p{index + 1}.txt",
                content_type=CONTENT_TYPE_TEXT,
                semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
            )
            if item is not None:
                content.append(item)
        return content

    def _extract_images_always(
        self,
        pdf: Any,
        storage: FileExtractCacheService,
        stem: str,
        scale: int,
    ) -> list[ExtractedDocumentContent]:
        import fitz

        matrix = fitz.Matrix(scale, scale)
        content: list[ExtractedDocumentContent] = []
        page_ext = self.PAGE_IMAGE_EXT
        fmt = self.PAGE_IMAGE_FORMAT

        def _make_page_image_writer(pix: Any):
            def writer(path: Path) -> None:
                write_rgb_to_path(
                    pix.samples,
                    pix.width,
                    pix.height,
                    path,
                    fmt,
                )

            return writer

        for index, page in enumerate(pdf):
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            content.append(
                storage.save_generated_file_content(
                    f"{stem}_p{index + 1}{page_ext}",
                    writer=_make_page_image_writer(pix),
                    content_type=CONTENT_TYPE_IMAGE,
                    semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
                )
            )

        return content

    def _extract_adaptive(
        self,
        pdf: Any,
        storage: FileExtractCacheService,
        stem: str,
        scale: int,
    ) -> list[ExtractedDocumentContent]:
        import fitz

        matrix = fitz.Matrix(scale, scale)
        content: list[ExtractedDocumentContent] = []
        page_ext = self.PAGE_IMAGE_EXT
        fmt = self.PAGE_IMAGE_FORMAT

        def _make_page_image_writer(pix: Any):
            def writer(path: Path) -> None:
                write_rgb_to_path(
                    pix.samples,
                    pix.width,
                    pix.height,
                    path,
                    fmt,
                )

            return writer

        for index, page in enumerate(pdf):
            text = self._get_page_text(page).strip()
            has_text = bool(text)
            has_images = self._page_has_images(page)
            has_large_images = self._page_has_large_image(
                page,
                self.ADAPTIVE_IMAGE_SIZE_SUM_THRESHOLD_PX,
            ) if has_images else False
            low_quality_text = has_text and is_low_quality_ocr_text(text)
            should_fallback_to_image = has_large_images or low_quality_text

            if has_text and not should_fallback_to_image:
                item = storage.save_text_content(
                    text,
                    f"{stem}_p{index + 1}.txt",
                    content_type=CONTENT_TYPE_TEXT,
                    semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
                )
                if item is not None:
                    content.append(item)
                continue

            if should_fallback_to_image:
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                content.append(
                    storage.save_generated_file_content(
                        f"{stem}_p{index + 1}{page_ext}",
                        writer=_make_page_image_writer(pix),
                        content_type=CONTENT_TYPE_IMAGE,
                        semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
                    )
                )

        return content

    def extract(
        self,
        source: SourceDocument,
        config: ExtractConfig,
        storage: FileExtractCacheService,
        document_hash: str,
    ) -> ExtractedDocument:
        algorithm = (self.get_setting(config, "algorithm", self.DEFAULT_PDF_ALGORITHM) or "").strip()
        if algorithm == self.PDF_ALGORITHM_SKIP:
            return ExtractedDocument(
                source=self._build_discovered_document(source),
                config=config,
                extract_hash=document_hash,
                content=[],
            )
        import fitz

        pdf_path = source.path_obj()
        pdf = fitz.open(pdf_path)
        stem = Path(source.filename).stem or "document"

        mode, scale = self._normalize_extract_params(config)

        try:
            if mode == self.PDF_EXTRACT_MODE_ONLY_TEXT:
                content = self._extract_only_text(
                    pdf=pdf,
                    storage=storage,
                    stem=stem,
                )
            elif mode == self.PDF_EXTRACT_MODE_IMAGES_ALWAYS:
                content = self._extract_images_always(
                    pdf=pdf,
                    storage=storage,
                    stem=stem,
                    scale=scale,
                )
            elif mode == self.PDF_EXTRACT_MODE_ADAPTIVE:
                content = self._extract_adaptive(
                    pdf=pdf,
                    storage=storage,
                    stem=stem,
                    scale=scale,
                )
            else:
                raise ValueError(f"Unknown PDF extract mode: {mode!r}")
        finally:
            pdf.close()

        return ExtractedDocument(
            source=self._build_discovered_document(source),
            config=config,
            extract_hash=document_hash,
            content=content,
        )
