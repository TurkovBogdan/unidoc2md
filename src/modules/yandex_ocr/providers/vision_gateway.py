"""Yandex Vision OCR gateway: text recognition with MD5 file cache."""

from __future__ import annotations

import base64
import json
import logging
import threading
from pathlib import Path
from typing import Any

import requests

from src.core.utils.hash import md5_string

from ..interfaces.response_logger import ResponseLoggerProtocol
from ..models import YandexOCRRequest, YandexOCRResult
from ..module import ModuleConfig, ModuleConfigStore, PROVIDER_CODE

logger = logging.getLogger(__name__)

OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"
TIMEOUT_SEC = 60
ENDPOINT_LOG_LABEL = "recognizeText"
RAW_RESPONSE_MAX_CHARS = 4096


class YandexOCRGateway:
    """
    OCR via Yandex Vision API.
    Auth: service account Api-Key only. Cache: cache_dir/{request_hash}.json.
    Configuration comes from ModuleConfigStore (module must be bootstrapped first).
    """

    def __init__(
        self,
        response_logger: ResponseLoggerProtocol | None = None,
    ) -> None:
        self._response_logger = (
            ModuleConfigStore.get().response_logger
            if response_logger is None
            else response_logger
        )

    @property
    def provider_code(self) -> str:
        """Provider id for logs and registries."""
        return PROVIDER_CODE

    def _config(self) -> ModuleConfig:
        return ModuleConfigStore.get()

    def _serialize_log_body(self, body: Any) -> str:
        """Convert a response or error payload to a compact log string."""
        try:
            raw = json.dumps(body, ensure_ascii=False)
        except (TypeError, ValueError):
            raw = str(body)
        if len(raw) > RAW_RESPONSE_MAX_CHARS:
            raw = raw[:RAW_RESPONSE_MAX_CHARS] + "..."
        return raw

    def _log_raw_response(
        self,
        endpoint: str,
        body: Any,
        *,
        status: int | None = None,
        is_error: bool = False,
        error_type: str | None = None,
    ) -> None:
        """Forward raw API payload to ResponseLoggerProtocol.debug() when a logger is set."""
        if self._response_logger is None:
            return
        kind = "error" if is_error else "response"
        err_label = (error_type or "-") if is_error else "-"
        status_str = str(status) if status is not None else "-"
        self._response_logger.debug(
            "gateway api | provider=%s endpoint=%s status=%s kind=%s error_type=%s | %s",
            self.provider_code,
            endpoint,
            status_str,
            kind,
            err_label,
            self._serialize_log_body(body),
        )

    def recognize_single(
        self,
        request: YandexOCRRequest,
        cancel_event: threading.Event | None = None,
    ) -> YandexOCRResult:
        """Recognize text for one image; return from cache when the request hash hits."""
        if cancel_event is not None and cancel_event.is_set():
            return YandexOCRResult(full_text="", content_hash=None)
        cache_dir = self._cache_dir_for_request(request)
        if cache_dir is not None:
            cached = self._get_from_cache(request, cache_dir)
            if cached is not None:
                return cached

        path = Path(request.image_path) if request.image_path else None
        if not path or not path.exists():
            logger.warning("yandex_ocr.file_missing path=%s", path)
            return YandexOCRResult(full_text="", content_hash=None)

        logger.debug("yandex_ocr.api_request file=%s", path.name)
        if cancel_event is not None and cancel_event.is_set():
            return YandexOCRResult(full_text="", content_hash=None)
        data = self._call_api(path, request, cancel_event=cancel_event)
        if cancel_event is not None and cancel_event.is_set():
            return YandexOCRResult(full_text="", content_hash=None)
        if cache_dir is not None:
            self._save_to_cache(request, data, cache_dir)
        text = self._extract_full_text(data)
        content_hash = md5_string(text) if text else None
        return YandexOCRResult(
            full_text=text,
            content_hash=content_hash,
            result=data,
            from_cache=False,
        )

    def _cache_dir_for_request(self, request: YandexOCRRequest) -> Path | None:
        """Cache directory: request.cache_path or config.cache_dir. None disables cache."""
        if request.cache_path:
            return Path(request.cache_path)
        return self._config().cache_dir

    def _cache_file_path(self, request: YandexOCRRequest, cache_dir: Path) -> Path:
        """Cache file path for the request hash (cache_dir already resolved)."""
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{request.get_request_hash()}.json"

    def _get_from_cache(self, request: YandexOCRRequest, cache_dir: Path) -> YandexOCRResult | None:
        """Return cached result on hit, else None."""
        cache_file = self._cache_file_path(request, cache_dir)
        if not cache_file.exists():
            return None
        logger.debug("yandex_ocr.cache_hit file=%s", cache_file.name)
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        text = self._extract_full_text(data)
        content_hash = data.get("full_text_hash") or (md5_string(text) if text else None)
        return YandexOCRResult(
            full_text=text,
            content_hash=content_hash,
            result=data,
            from_cache=True,
        )

    def _save_to_cache(self, request: YandexOCRRequest, data: dict, cache_dir: Path) -> None:
        """Persist flattened textAnnotation fields (full_text, full_text_hash, entities, tables, …)."""
        cache_file = self._cache_file_path(request, cache_dir)
        data_to_save = self._data_for_cache(data)
        cache_file.write_text(
            json.dumps(data_to_save, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.debug("yandex_ocr.cache_saved file=%s", cache_file.name)

    def _mime_type_for_path(self, path: Path) -> str:
        """Request body mimeType from file extension (docs: JPEG, PNG, PDF)."""
        suffix = (path.suffix or "").lower()
        if suffix in (".png",):
            return "PNG"
        if suffix in (".pdf",):
            return "PDF"
        if suffix in (".jpg", ".jpeg",):
            return "JPEG"
        return "JPEG"

    def _data_for_cache(self, data: dict) -> dict:
        """Flat cache object: textAnnotation without nested result/textAnnotation, without blocks/width/height; full_text + full_text_hash."""
        try:
            ta = data.get("result", {}).get("textAnnotation")
            if not isinstance(ta, dict):
                return {}
            ta = dict(ta)
            for key in ("blocks", "width", "height"):
                ta.pop(key, None)
            raw_text = ta.pop("fullText", "") or ""
            ta["full_text"] = raw_text
            ta["full_text_hash"] = md5_string(raw_text) if raw_text else ""
            return ta
        except (KeyError, TypeError):
            return {}

    def _extract_full_text(self, response: dict) -> str:
        """Extract text from API response (result.textAnnotation.fullText) or cache (full_text)."""
        ta = response.get("result", {}).get("textAnnotation") if "result" in response else response
        if not ta:
            return ""
        return ta.get("full_text") or ta.get("fullText") or ""

    def _call_api(
        self,
        image_path: Path,
        request: YandexOCRRequest,
        cancel_event: threading.Event | None = None,
    ) -> dict:
        if cancel_event is not None and cancel_event.is_set():
            return {}
        config = self._config()
        token = (config.api_config.key_secret or "").strip()
        auth_header = f"Api-Key {token}" if token else ""
        content_b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "x-data-logging-enabled": "true",
        }
        language_codes = request.language if request.language else ["ru", "en"]
        body = {
            "mimeType": self._mime_type_for_path(image_path),
            "languageCodes": language_codes,
            "model": request.model,
            "content": content_b64,
        }
        try:
            resp = requests.post(
                OCR_URL,
                headers=headers,
                json=body,
                timeout=TIMEOUT_SEC,
            )
        except Exception as e:
            self._log_raw_response(
                ENDPOINT_LOG_LABEL,
                str(e),
                is_error=True,
                error_type=type(e).__name__,
            )
            raise
        if not resp.ok:
            status = resp.status_code
            try:
                err_body = resp.json()
            except Exception:
                err_body = resp.text or "(empty)"
            self._log_raw_response(
                ENDPOINT_LOG_LABEL,
                err_body,
                status=status,
                is_error=True,
                error_type="HTTPError",
            )
            hint = ""
            if status == 403:
                hint = (
                    "\n  Possible 403 causes: invalid API key, missing ai.vision.user role, or service disabled."
                )
            elif status == 401:
                hint = "\n  401: invalid or missing Api-Key."
            logger.error("yandex_ocr.api_http_error status=%d body_prefix=%s%s", status, resp.text[:300], hint)
            resp.raise_for_status()
        data = resp.json()
        self._log_raw_response(ENDPOINT_LOG_LABEL, data, status=resp.status_code)
        return data
