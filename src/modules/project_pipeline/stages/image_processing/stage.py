"""Этап image_processing: обработка отдельных единиц контента документа."""

from __future__ import annotations

import threading
from typing import Any, TypedDict

from src.core.utils.hash import md5_file
from src.modules.file_extract.models import (
    ExtractedDocument,
    ExtractedDocumentContent,
)
from src.modules.file_extract.constants import (
    MIME_IMAGE_GIF,
    MIME_IMAGE_JPEG,
    MIME_IMAGE_PNG,
    MIME_IMAGE_WEBP,
    MIME_TEXT_PLAIN,
)
from src.modules.file_extract.models import (
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
)
from src.modules.project.sections.image_processing_config import ImageProcessingConfig
from src.modules.project.sections.pipeline_config import (
    IMAGE_PROCESSING_THREADS_DEFAULT,
    IMAGE_PROCESSING_THREADS_MAX,
    IMAGE_PROCESSING_THREADS_MIN,
    KEY_IMAGE_PROCESSING_THREADS,
)
from ..base import BasePipelineStage
from ...models import (
    PipelineContext,
    StageResult,
)
from ..parallel import run_parallel_stage

# Системный промпт этапа Vision: OCR-инструкция. Доп. текст из конфига (vision_system_prompt) добавляется после.
VISION_LLM_SYSTEM_PROMPT = """You are a perfect OCR (Optical Character Recognition) machine. Your ONLY task is to extract and return the text visible in the provided image.

Rules you MUST follow:

* Transcribe all characters, words, symbols and punctuation from the image.
* You MAY correct obvious typos and spelling mistakes if they are clearly unintentional.
* Preserve original formatting as closely as possible: use line breaks for new lines, spaces for indentation, markdown tables if there is a table, bullet points if there are lists.
* If text is in multiple languages, keep them exactly as shown.
* If there are multiple blocks of text (headings, paragraphs, captions), keep the same visual structure using blank lines between blocks.
* For tables: always format them as standard Markdown tables with aligned separators (minimum three dashes per column). Example:

| Column A | Column B |
| --- | --- |
| Value 1  | Value 2  |

* NEVER add explanations, summaries, comments, or any extra text.
* If NO text is visible in the image at all, respond with exactly this one line and nothing else: "No text detected"

Output ONLY the transcribed text.
"""


def _compose_vision_llm_system_prompt(user_instructions: str | None) -> str:
    """Константа этапа + при необходимости доп. инструкции из конфига (vision_system_prompt)."""
    base = (VISION_LLM_SYSTEM_PROMPT or "").strip()
    add_raw = (user_instructions or "").strip() if isinstance(user_instructions, str) else ""
    if not add_raw:
        return base
    return f"{base}\n\n{add_raw}"


class _VisionUsageAcc(TypedDict):
    prompt: int
    reasoning: int
    completion: int
    total: int
    cache_hits: int
    api_calls: int


class ImageProcessingStage(BasePipelineStage):
    """Image processing в извлечённых документах: OCR или Vision LLM."""

    _vision_llm_call_lock = threading.Lock()
    # На время run() для vision_only / ocr_only: lock + счётчики (LLM токены или OCR кеш/API).
    _image_usage_state: tuple[threading.Lock, _VisionUsageAcc] | None = None

    @property
    def stage_id(self) -> str:
        return "image_processing"

    def is_enabled(self, context: PipelineContext) -> bool:
        logic = self._get_processing_logic(context.config)
        return logic in (
            ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.ocr_only,
            ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.vision_only,
        )

    def run(self, context: PipelineContext, input_result: object) -> StageResult:
        documents: list[ExtractedDocument | None] = (
            input_result if isinstance(input_result, list) else []
        )
        if not self.is_enabled(context):
            context.logger.info("Image processing: stage skipped")
            return StageResult.ok(documents)
        threads = self._get_max_workers(context.config)
        logic = self._get_processing_logic(context.config)
        processed_documents: list[ExtractedDocument | None] = []
        task_items: list[tuple[tuple[int, int, str], ExtractedDocumentContent]] = []
        for doc_index, document in enumerate(documents):
            if document is None:
                processed_documents.append(document)
                continue
            copied_content = list(document.content)
            processed_documents.append(
                ExtractedDocument(
                    source=document.source,
                    config=document.config,
                    extract_hash=document.extract_hash,
                    content_hash=document.content_hash,
                    content=copied_content,
                )
            )
            for item_index, item in enumerate(document.content):
                if item.content_type != "image":
                    continue
                task_items.append(
                    ((doc_index, item_index, document.source.filename), item)
                )
        total_images = len(task_items)
        total_documents = sum(1 for d in documents if d is not None)
        context.logger.info(
            "Image processing: logic=%s, queue %s images from %s documents, workers=%s",
            logic,
            total_images,
            total_documents,
            threads,
        )

        vision_provider = ""
        vision_model = ""
        price_in: float | None = None
        price_out: float | None = None
        usage_lock = threading.Lock()
        usage_acc: _VisionUsageAcc = {
            "prompt": 0,
            "reasoning": 0,
            "completion": 0,
            "total": 0,
            "cache_hits": 0,
            "api_calls": 0,
        }

        if logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.vision_only:
            section = context.config.image_processing or {}
            K = ImageProcessingConfig.IMAGE_PROCESSING_KEYS
            vision_provider = (section.get(K.vision_provider) or "").strip()
            vision_model = (section.get(K.vision_model) or "").strip()
            price_in, price_out = self._resolve_vision_registry_prices(
                vision_provider,
                vision_model,
            )
            context.logger.info(
                "Image processing: vision provider=%s, model=%s, "
                "input price per 1M=%s, output price per 1M=%s",
                vision_provider or "—",
                vision_model or "—",
                price_in if price_in is not None else "—",
                price_out if price_out is not None else "—",
            )
            self._image_usage_state = (usage_lock, usage_acc)
        elif logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.ocr_only:
            self._image_usage_state = (usage_lock, usage_acc)
        else:
            self._image_usage_state = None

        def _payload() -> dict[str, Any]:
            return self._image_processing_summary_payload(
                logic,
                vision_provider=vision_provider,
                vision_model=vision_model,
                price_input_per_million=price_in,
                price_output_per_million=price_out,
                usage_acc=usage_acc,
            )

        def _emit_progress(images_done: int, images_total: int) -> None:
            self._emit_image_processing_progress(
                context,
                logic=logic,
                vision_provider=vision_provider,
                vision_model=vision_model,
                price_in=price_in,
                price_out=price_out,
                usage_lock=usage_lock,
                usage_acc=usage_acc,
                images_done=images_done,
                images_total=images_total,
            )

        try:
            if total_images == 0:
                context.logger.info(
                    "Image processing: no images to process"
                )
                return StageResult.ok(processed_documents, payload=[_payload()])

            _emit_progress(0, total_images)

            def process_one(item: ExtractedDocumentContent) -> ExtractedDocumentContent:
                return self._execute_item(context, item)

            def handle_result(
                meta: tuple[int, int, str], result: ExtractedDocumentContent
            ) -> None:
                doc_index, item_index, _ = meta
                doc = processed_documents[doc_index]
                if doc is not None:
                    doc.content[item_index] = result

            def on_images_progress(done: int, total: int) -> None:
                _emit_progress(done, total)

            run_parallel_stage(
                stage_name="Image processing",
                logger=context.logger,
                task_items=task_items,
                max_workers=threads,
                cancel_event=context.cancel_event,
                worker=process_one,
                handle_result=handle_result,
                describe_item=lambda meta: f"{meta[2]}[{meta[1] + 1}]",
                on_progress=on_images_progress,
            )
            processed_count = sum(
                1
                for doc in processed_documents
                if doc is not None
                and any(
                    item.content_type == "text" and item.path is None
                    for item in doc.content
                )
            )
            context.logger.info(
                "Image processing: processed %s documents", processed_count
            )
            return StageResult.ok(processed_documents, payload=[_payload()])
        finally:
            self._image_usage_state = None

    def _get_processing_logic(self, config: Any) -> str:
        section = config.image_processing or {}
        return (
            section.get(
                ImageProcessingConfig.IMAGE_PROCESSING_KEYS.image_processing_logic
            )
            or ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.skip
        ).strip().lower()

    def _get_max_workers(self, config: Any) -> int:
        logic = self._get_processing_logic(config)
        if logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.skip:
            return 0
        if logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.ocr_only:
            return 1
        threads = config.pipeline.get(
            KEY_IMAGE_PROCESSING_THREADS,
            IMAGE_PROCESSING_THREADS_DEFAULT,
        )
        return max(
            IMAGE_PROCESSING_THREADS_MIN,
            min(IMAGE_PROCESSING_THREADS_MAX, int(threads)),
        )

    def _emit_image_processing_progress(
        self,
        context: PipelineContext,
        *,
        logic: str,
        vision_provider: str,
        vision_model: str,
        price_in: float | None,
        price_out: float | None,
        usage_lock: threading.Lock,
        usage_acc: _VisionUsageAcc,
        images_done: int,
        images_total: int,
    ) -> None:
        """Снимок для UI: прогресс по изображениям и накопленные vision-токены/стоимость."""
        sink = context.progress_sink
        if sink is None:
            return
        with usage_lock:
            snap: _VisionUsageAcc = {
                "prompt": usage_acc["prompt"],
                "reasoning": usage_acc["reasoning"],
                "completion": usage_acc["completion"],
                "total": usage_acc["total"],
                "cache_hits": usage_acc["cache_hits"],
                "api_calls": usage_acc["api_calls"],
            }
        summary = self._image_processing_summary_payload(
            logic,
            vision_provider=vision_provider,
            vision_model=vision_model,
            price_input_per_million=price_in,
            price_output_per_million=price_out,
            usage_acc=snap,
        )
        envelope: dict[str, Any] = {
            **summary,
            "images_done": images_done,
            "images_total": images_total,
        }
        sink("image_processing", envelope)

    @staticmethod
    def _resolve_vision_registry_prices(
        provider: str,
        model: str,
    ) -> tuple[float | None, float | None]:
        """Цены из реестра llm_models_registry (USD за 1M токенов)."""
        if not provider or not model:
            return None, None
        try:
            from src.modules.llm_models_registry import LLMModelManager

            rec = LLMModelManager().get_record(f"{provider}@{model}")
        except RuntimeError:
            return None, None
        if rec is None:
            return None, None
        return (
            LLMModelManager.optional_price_per_million(rec.get("price_input")),
            LLMModelManager.optional_price_per_million(rec.get("price_output")),
        )

    @staticmethod
    def _image_processing_summary_payload(
        logic: str,
        *,
        vision_provider: str,
        vision_model: str,
        price_input_per_million: float | None,
        price_output_per_million: float | None,
        usage_acc: _VisionUsageAcc,
    ) -> dict[str, Any]:
        """Сводка для UI: vision — токены и цены; ocr — только кеш/API (без стоимости)."""
        vision_block: dict[str, Any] | None = None
        if logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.vision_only:
            vision_block = {
                "billing": "vision",
                "provider": vision_provider,
                "model": vision_model,
                "price_input_per_million": price_input_per_million,
                "price_output_per_million": price_output_per_million,
                "tokens_prompt": int(usage_acc["prompt"]),
                "tokens_total": int(usage_acc["total"]),
                "tokens_reasoning": int(usage_acc["reasoning"]),
                "tokens_completion": int(usage_acc["completion"]),
                "cache_hits": int(usage_acc["cache_hits"]),
                "api_calls": int(usage_acc["api_calls"]),
            }
        elif logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.ocr_only:
            vision_block = {
                "billing": "ocr",
                "cache_hits": int(usage_acc["cache_hits"]),
                "api_calls": int(usage_acc["api_calls"]),
            }
        return {"logic": logic, "vision": vision_block}

    def _execute_item(
        self,
        context: PipelineContext,
        item: ExtractedDocumentContent,
    ) -> ExtractedDocumentContent:
        if context.cancel_event is not None and context.cancel_event.is_set():
            return item
        if item.content_type != "image":
            return item
        if item.semantic_type != SEMANTIC_TYPE_REQUIRED_DETECTION:
            return item
        logic = self._get_processing_logic(context.config)
        if logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.ocr_only:
            return self._ocr_processing(context, item)
        if logic == ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.vision_only:
            return self._vision_processing(context, item)
        return item

    def _ocr_processing(
        self,
        context: PipelineContext,
        item: ExtractedDocumentContent,
    ) -> ExtractedDocumentContent:
        from pathlib import Path

        from src.modules.yandex_ocr import YandexOCRGateway, YandexOCRRequest

        cache_dir = Path(context.config.paths.cache_ocr)
        section = context.config.image_processing or {}
        model = (
            section.get(ImageProcessingConfig.IMAGE_PROCESSING_KEYS.ocr_model)
            or "page"
        )
        path = item.path_obj()
        if path is None or not path.exists():
            return item
        gateway = YandexOCRGateway()
        image_hash = item.content_hash or md5_file(path)
        request = YandexOCRRequest(
            model=model,
            image_path=path,
            image_hash=image_hash,
            cache_path=cache_dir,
        )
        result = gateway.recognize_single(
            request, cancel_event=context.cancel_event
        )
        usage_state = self._image_usage_state
        if usage_state is not None:
            lock, acc = usage_state
            with lock:
                if result.from_cache:
                    acc["cache_hits"] += 1
                elif result.full_text or result.result:
                    acc["api_calls"] += 1
        if context.cancel_event is not None and context.cancel_event.is_set():
            return item
        return item.replace_content(
            content_type="text",
            semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
            path=None,
            mime_type=MIME_TEXT_PLAIN,
            content_hash=result.content_hash,
            value=result.full_text,
        )

    def _vision_processing(
        self,
        context: PipelineContext,
        item: ExtractedDocumentContent,
    ) -> ExtractedDocumentContent:
        import base64
        from pathlib import Path

        from src.modules.llm_providers import LLMProvider
        from src.modules.llm_providers.module import (
            ModuleStore,
            llm_providers_set_cache_path,
        )
        from src.modules.llm_providers.schemas.chat import (
            LLMChatMessage,
            LLMChatMessageImage,
            LLMChatMessageText,
            LLMChatReasoningEffort,
            LLMChatRequest,
            LLMChatRole,
        )

        section = context.config.image_processing or {}
        K = ImageProcessingConfig.IMAGE_PROCESSING_KEYS
        provider = (section.get(K.vision_provider) or "").strip()
        model = (section.get(K.vision_model) or "").strip()
        if not provider or not model:
            return item
        path = item.path_obj()
        if path is None or not path.exists():
            return item
        if context.cancel_event is not None and context.cancel_event.is_set():
            return item
        try:
            image_bytes = path.read_bytes()
        except OSError:
            return item
        image_b64 = base64.standard_b64encode(image_bytes).decode("ascii")
        ext = (path.suffix or "").lower()
        mime_map = {
            ".png": MIME_IMAGE_PNG,
            ".jpg": MIME_IMAGE_JPEG,
            ".jpeg": MIME_IMAGE_JPEG,
            ".webp": MIME_IMAGE_WEBP,
            ".gif": MIME_IMAGE_GIF,
        }
        mime = mime_map.get(ext, MIME_IMAGE_PNG)
        user_instructions = (
            section.get(K.vision_system_prompt)
            or ImageProcessingConfig.IMAGE_PROCESSING_DEFAULTS.vision_system_prompt
        ) or ""
        system_prompt = _compose_vision_llm_system_prompt(user_instructions)
        reason_raw = (section.get(K.vision_reasoning) or "disabled").strip().lower()
        try:
            reasoning = LLMChatReasoningEffort(reason_raw)
        except ValueError:
            reasoning = LLMChatReasoningEffort.DISABLED
        t = section.get(K.vision_temperature)
        temperature = (
            ImageProcessingConfig.IMAGE_PROCESSING_DEFAULTS.vision_temperature
        )
        if t is not None:
            try:
                temperature = max(0.0, min(2.0, float(t)))
            except (TypeError, ValueError):
                pass
        messages = []
        if system_prompt:
            messages.append(
                LLMChatMessage(
                    role=LLMChatRole.SYSTEM,
                    content=[LLMChatMessageText(message=system_prompt)],
                )
            )
        messages.append(
            LLMChatMessage(
                role=LLMChatRole.USER,
                content=[LLMChatMessageImage(mime=mime, base64=image_b64)],
            )
        )
        cache_dir = Path(context.config.paths.cache_vision)
        cache_dir.mkdir(parents=True, exist_ok=True)
        request = LLMChatRequest(
            provider=provider,
            model=model,
            messages=messages,
            reasoning=reasoning,
            temperature=temperature,
            max_tokens=4096,
        )
        try:
            with self._vision_llm_call_lock:
                prev_cache = None
                try:
                    prev_cache = ModuleStore.get().cache_path
                except RuntimeError:
                    pass
                llm = LLMProvider()
                llm.set_cache_path(cache_dir)
                try:
                    response = llm.chat(request, cache=True)
                finally:
                    llm_providers_set_cache_path(prev_cache)
        except Exception as e:
            from src.core.logger import get_system_logger

            get_system_logger().warning(
                "vision_processing error path=%s: %s", path, e, exc_info=True
            )
            raise
        if context.cancel_event is not None and context.cancel_event.is_set():
            return item
        usage_state = self._image_usage_state
        if usage_state is not None:
            lock, acc = usage_state
            with lock:
                if response.cache:
                    acc["cache_hits"] += 1
                else:
                    acc["api_calls"] += 1
                    if response.tokens_usage is not None:
                        u = response.tokens_usage
                        pr = int(u.prompt)
                        reas = int(u.reasoning)
                        comp = int(u.completion)
                        tot = int(u.total)
                        if tot <= 0:
                            tot = pr + reas + comp
                        acc["prompt"] += pr
                        acc["reasoning"] += reas
                        acc["completion"] += comp
                        acc["total"] += tot
        text_parts = []
        if response.message and response.message.content:
            for block in response.message.content:
                if isinstance(block, LLMChatMessageText):
                    text_parts.append(block.message)
        result_text = "\n".join(text_parts).strip() if text_parts else ""
        if result_text.strip().lower() == "no text detected":
            result_text = ""
        content_hash = request.cache_key()
        return item.replace_content(
            content_type="text",
            semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
            path=None,
            mime_type=MIME_TEXT_PLAIN,
            content_hash=content_hash,
            value=result_text,
        )
