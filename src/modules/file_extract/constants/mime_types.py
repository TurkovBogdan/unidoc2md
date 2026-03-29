"""MIME constants for file_extract."""

from __future__ import annotations

import mimetypes

MIME_TEXT_PLAIN = "text/plain"
MIME_TEXT_MARKDOWN = "text/markdown"

MIME_IMAGE_PNG = "image/png"
MIME_IMAGE_JPEG = "image/jpeg"
MIME_IMAGE_WEBP = "image/webp"
MIME_IMAGE_GIF = "image/gif"

MIME_APPLICATION_PDF = "application/pdf"


def guess_mime_type(path_or_ext: str, fallback: str | None = None) -> str | None:
    value = (path_or_ext or "").lower().strip()
    if not value:
        return fallback
    if "." not in value:
        value = f".{value}"
    guessed, _ = mimetypes.guess_type(f"file{value}")
    return guessed or fallback
