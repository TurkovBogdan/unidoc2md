"""Exceptions for the yandex_ocr module."""

from __future__ import annotations


class YandexOCRError(Exception):
    """Base exception for the Yandex OCR module."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class YandexOCRAuthError(YandexOCRError):
    """Authentication failure (401, 403, invalid Api-Key)."""


class YandexOCRTransportError(YandexOCRError):
    """Network/transport error (timeout, connection)."""


class YandexOCRResponseError(YandexOCRError):
    """Invalid or unexpected API response."""
