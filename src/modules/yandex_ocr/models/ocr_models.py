"""Request and result models for Yandex Vision OCR API calls."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.core.utils.hash import md5_string

from ..module import DEFAULT_MODEL

DEFAULT_LANGUAGE: list[str] = ["ru", "en"]


@dataclass
class YandexOCRRequest:
    """Recognition parameters: model, languages, image path, hash, optional cache path."""

    model: str = DEFAULT_MODEL
    language: list[str] = field(default_factory=lambda: list(DEFAULT_LANGUAGE))
    image_path: Path | str | None = None
    image_hash: str | None = None
    cache_path: Path | None = None

    def get_request_hash(self) -> str:
        """MD5 of ``model + '-' + languages joined with '-' + '-' + image_hash``."""
        lang_part = "-".join(self.language) if self.language else ""
        combined = f"{self.model}-{lang_part}-{self.image_hash or ''}"
        return md5_string(combined)


@dataclass
class YandexOCRResult:
    """OCR result for one image: full text and raw API payload."""

    full_text: str = ""
    content_hash: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    #: True if the response came from disk cache (no API call).
    from_cache: bool = False
