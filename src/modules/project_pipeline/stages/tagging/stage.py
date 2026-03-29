"""Этап tagging: вызов LLM для получения тегов документа, накопление набора тегов."""

from __future__ import annotations

import threading
import time
from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from src.core.logger import get_system_logger
from src.core.logger.system_logger_store import SystemLoggerStore
from src.modules.markdown.models import MarkdownDocument
from src.modules.project.sections.pipeline_config import (
    KEY_TAGGING_THREADS,
    TAGGING_THREADS_DEFAULT,
    TAGGING_THREADS_MAX,
    TAGGING_THREADS_MIN,
)
from src.modules.project.sections.tagging_config import (
    TAGGING_DEFAULTS,
    TAGGING_KEYS,
    TAGGING_MODES,
    TAGGING_PAYLOAD_LOGIC,
    TaggingConfig,
)
from ..base import BasePipelineStage
from ...models import (
    PipelineContext,
    StageResult,
)
from ...utils import (
    LLMUsageAcc,
    accumulate_llm_usage,
    empty_llm_usage_acc,
    resolve_llm_registry_prices,
)
from .tagging_prompt_builder import TaggingPromptBuilder
from .tagging_result_parser import TaggingResultParser
from .tagging_tag_normalize import normalize_tag, parse_start_tag_set

TAGGING_LLM_MAX_COMPLETION_TOKENS = 2048


def _resolve_tagging_parallel_workers(pipeline: dict[str, Any] | None, doc_count: int) -> int:
    """Число потоков для параллельного тегирования из секции pipeline (не больше числа документов)."""
    if doc_count <= 0:
        return 1
    pl = pipeline if isinstance(pipeline, dict) else {}
    raw = pl.get(KEY_TAGGING_THREADS, TAGGING_THREADS_DEFAULT)
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = TAGGING_THREADS_DEFAULT
    n = max(TAGGING_THREADS_MIN, min(TAGGING_THREADS_MAX, n))
    return max(1, min(n, doc_count))


class TaggingStage(BasePipelineStage):
    """После markdown: для каждого документа запрос в LLM (разметка + набор тегов), запись тегов в документ, накопление набора."""

    @staticmethod
    def _normalize_doc_tags_for_tagging(
        document: MarkdownDocument, tag_format: str
    ) -> MarkdownDocument:
        seen: set[str] = set()
        tags: list[str] = []
        for t in document.tags or []:
            n = normalize_tag(str(t), tag_format)
            if n and n not in seen:
                seen.add(n)
                tags.append(n)
        return replace(document, tags=tags)

    @staticmethod
    def _tagging_summary_payload(
        provider: str,
        model: str,
        price_input_per_million: float | None,
        price_output_per_million: float | None,
        usage_acc: LLMUsageAcc,
    ) -> dict[str, Any]:
        """Формат как у markdown-этапа: logic + llm (для GUI и контроллера)."""
        llm_block: dict[str, Any] = {
            "billing": "llm",
            "provider": provider,
            "model": model,
            "price_input_per_million": price_input_per_million,
            "price_output_per_million": price_output_per_million,
            "tokens_prompt": int(usage_acc["prompt"]),
            "tokens_total": int(usage_acc["total"]),
            "tokens_reasoning": int(usage_acc["reasoning"]),
            "tokens_completion": int(usage_acc["completion"]),
            "cache_hits": int(usage_acc["cache_hits"]),
            "api_calls": int(usage_acc["api_calls"]),
        }
        return {"logic": TAGGING_PAYLOAD_LOGIC.llm, "llm": llm_block}

    def _emit_tagging_idle_progress(
        self,
        context: PipelineContext,
        *,
        payload_logic: str,
        documents_total: int,
    ) -> None:
        """Прогресс без LLM: режим «Пропустить» или нет провайдера/модели."""
        sink = context.progress_sink
        if sink is None:
            return
        sink(
            "tagging",
            {
                "logic": payload_logic,
                "llm": None,
                "documents_done": documents_total,
                "documents_total": documents_total,
            },
        )

    def _emit_tagging_progress(
        self,
        context: PipelineContext,
        *,
        provider: str,
        model: str,
        price_in: float | None,
        price_out: float | None,
        usage_acc: LLMUsageAcc,
        documents_done: int,
        documents_total: int,
    ) -> None:
        sink = context.progress_sink
        if sink is None:
            return
        summary = self._tagging_summary_payload(
            provider,
            model,
            price_in,
            price_out,
            usage_acc,
        )
        envelope: dict[str, Any] = {
            **summary,
            "documents_done": documents_done,
            "documents_total": documents_total,
        }
        sink("tagging", envelope)

    @property
    def stage_id(self) -> str:
        return "tagging"

    def is_enabled(self, context: PipelineContext) -> bool:
        """Этап всегда выполняется (как markdown): внутри run учитывается режим и провайдер."""
        return True

    def run(self, context: PipelineContext, input_result: object) -> StageResult:
        documents: list[MarkdownDocument] = (
            input_result if isinstance(input_result, list) else []
        )
        if not documents:
            context.logger.info("Tagging: no documents, skip")
            return StageResult.ok(documents)

        section = context.config.tagging or {}
        K = TAGGING_KEYS
        M = TAGGING_MODES
        mode_raw = section.get(K.tagging_mode)
        default_mode = TAGGING_DEFAULTS.tagging_mode
        if mode_raw is None or (isinstance(mode_raw, str) and not str(mode_raw).strip()):
            mode = default_mode
        else:
            mode = str(mode_raw).strip().lower()
        # Устаревшее значение конфига → линейный режим
        if mode == "create_document_tags":
            mode = M.create_document_tags_linear
        if mode not in M.valid_codes:
            mode = default_mode

        n_docs = len(documents)
        if mode == M.skip:
            context.logger.info("Tagging: skip mode, documents unchanged")
            self._emit_tagging_idle_progress(
                context,
                payload_logic=TAGGING_PAYLOAD_LOGIC.skip,
                documents_total=n_docs,
            )
            return StageResult.ok(
                documents,
                payload=[{"logic": TAGGING_PAYLOAD_LOGIC.skip, "llm": None}],
            )

        create_tags_field = TaggingConfig.coerce_bool(
            section.get(K.create_tags_field), TAGGING_DEFAULTS.create_tags_field
        )
        if not create_tags_field:
            context.logger.info(
                "Tagging: create_tags_field off — LLM not invoked"
            )
            self._emit_tagging_idle_progress(
                context,
                payload_logic=TAGGING_PAYLOAD_LOGIC.create_tags_field_off,
                documents_total=n_docs,
            )
            return StageResult.ok(
                documents,
                payload=[{"logic": TAGGING_PAYLOAD_LOGIC.create_tags_field_off, "llm": None}],
            )

        provider = (section.get(K.llm_provider) or "").strip()
        model = (section.get(K.llm_model) or "").strip()
        if not provider or not model:
            context.logger.info(
                "Tagging: tag creation mode but provider/model missing — LLM not invoked"
            )
            self._emit_tagging_idle_progress(
                context,
                payload_logic=TAGGING_PAYLOAD_LOGIC.no_llm,
                documents_total=n_docs,
            )
            return StageResult.ok(
                documents,
                payload=[{"logic": TAGGING_PAYLOAD_LOGIC.no_llm, "llm": None}],
            )

        tag_fmt = TaggingConfig.coerce_tag_format(
            section.get(K.tag_format), TAGGING_DEFAULTS.tag_format
        )
        start_raw = section.get(K.start_tag_set) or TAGGING_DEFAULTS.start_tag_set or ""
        tag_set: list[str] = parse_start_tag_set(
            str(start_raw) if start_raw else "", tag_fmt
        )
        documents = [
            self._normalize_doc_tags_for_tagging(d, tag_fmt) for d in documents
        ]
        documents.sort(key=lambda d: str(d.relative_path).casefold())
        context.logger.info(
            "Tagging: start, documents=%s, initial_tags=%s",
            len(documents),
            len(tag_set),
        )

        price_in, price_out = resolve_llm_registry_prices(provider, model)
        context.logger.info(
            "Tagging: LLM provider=%s, model=%s, input price per 1M=%s, output price per 1M=%s",
            provider or "—",
            model or "—",
            price_in if price_in is not None else "—",
            price_out if price_out is not None else "—",
        )
        usage_acc = empty_llm_usage_acc()
        usage_lock = threading.Lock()

        def _payload_snap() -> dict[str, Any]:
            return self._tagging_summary_payload(
                provider,
                model,
                price_in,
                price_out,
                usage_acc,
            )

        def _emit(done: int, total: int) -> None:
            self._emit_tagging_progress(
                context,
                provider=provider,
                model=model,
                price_in=price_in,
                price_out=price_out,
                usage_acc=usage_acc,
                documents_done=done,
                documents_total=total,
            )

        _emit(0, n_docs)

        cache_dir = Path(context.config.paths.cache_llm)
        cache_dir.mkdir(parents=True, exist_ok=True)
        prev_cache = None
        try:
            from src.modules.llm_providers.module import (
                ModuleStore,
                llm_providers_set_cache_path,
            )
            try:
                prev_cache = ModuleStore.get().cache_path
            except RuntimeError:
                pass
            llm_providers_set_cache_path(cache_dir)
            try:
                if mode == M.create_document_tags_linear:
                    for i, doc in enumerate(documents):
                        if context.cancel_event is not None and context.cancel_event.is_set():
                            break
                        tagged = self._tag_one(
                            context, doc, tag_set, tag_fmt, usage_acc
                        )
                        documents[i] = tagged
                        for t in tagged.tags:
                            if t not in tag_set:
                                tag_set.append(t)
                        context.logger.info(
                            "Tagging: done %s/%s (%s)",
                            i + 1,
                            n_docs,
                            doc.relative_path,
                        )
                        _emit(i + 1, n_docs)
                else:
                    tag_set_lock = threading.Lock()
                    workers = _resolve_tagging_parallel_workers(
                        context.config.pipeline, n_docs
                    )

                    def _process_index(i: int) -> tuple[int, MarkdownDocument]:
                        doc = documents[i]
                        if context.cancel_event is not None and context.cancel_event.is_set():
                            return i, doc
                        with tag_set_lock:
                            snapshot = list(tag_set)
                        tagged = self._tag_one(
                            context,
                            doc,
                            snapshot,
                            tag_fmt,
                            usage_acc,
                            usage_lock=usage_lock,
                        )
                        with tag_set_lock:
                            for t in tagged.tags:
                                if t not in tag_set:
                                    tag_set.append(t)
                        return i, tagged

                    executor = ThreadPoolExecutor(max_workers=workers)
                    try:
                        futures = [
                            executor.submit(_process_index, i) for i in range(n_docs)
                        ]
                        done_n = 0
                        for fut in as_completed(futures):
                            if context.cancel_event is not None and context.cancel_event.is_set():
                                break
                            i, tagged = fut.result()
                            documents[i] = tagged
                            done_n += 1
                            context.logger.info(
                                "Tagging: done %s/%s (%s)",
                                done_n,
                                n_docs,
                                tagged.relative_path,
                            )
                            _emit(done_n, n_docs)
                    finally:
                        executor.shutdown(wait=False, cancel_futures=True)
            finally:
                llm_providers_set_cache_path(prev_cache)
        except ImportError:
            raise

        context.logger.info("Tagging: processed %s documents", len(documents))
        return StageResult.ok(documents, payload=[_payload_snap()])

    def _tag_one(
        self,
        context: PipelineContext,
        document: MarkdownDocument,
        current_tag_set: list[str],
        tag_format: str,
        usage_acc: LLMUsageAcc | None = None,
        *,
        usage_lock: threading.Lock | None = None,
    ) -> MarkdownDocument:
        """Один запрос к LLM: в system — промпт и накопленные теги; в user — только содержимое документа."""
        from src.modules.llm_providers import LLMProvider
        from src.modules.llm_providers.schemas.chat import (
            LLMChatMessage,
            LLMChatMessageText,
            LLMChatReasoningEffort,
            LLMChatRequest,
            LLMChatRole,
        )

        if context.cancel_event is not None and context.cancel_event.is_set():
            return document

        section = context.config.tagging or {}
        K = TAGGING_KEYS
        provider = (section.get(K.llm_provider) or "").strip()
        model = (section.get(K.llm_model) or "").strip()
        if not provider or not model:
            return document

        reason_raw = (
            (section.get(K.llm_reasoning) or TAGGING_DEFAULTS.llm_reasoning)
        ).strip().lower()
        try:
            reasoning = LLMChatReasoningEffort(reason_raw)
        except ValueError:
            reasoning = LLMChatReasoningEffort.DISABLED

        t = section.get(K.llm_temperature)
        temperature = getattr(TAGGING_DEFAULTS, "llm_temperature", 0.3)
        if t is not None:
            try:
                temperature = max(0.0, min(2.0, float(t)))
            except (TypeError, ValueError):
                pass

        raw_supplement = section.get(K.llm_additional_instructions)
        user_supplement = raw_supplement if isinstance(raw_supplement, str) else None
        description = TaggingConfig.coerce_bool(
            section.get(K.create_description_field), TAGGING_DEFAULTS.create_description_field
        )
        date = TaggingConfig.coerce_bool(
            section.get(K.create_date_field), TAGGING_DEFAULTS.create_date_field
        )
        system_prompt = TaggingPromptBuilder.build_tagging_system_prompt(
            user_supplement=user_supplement,
            description=description,
            date=date,
            tag_set=current_tag_set,
            tag_format=tag_format,
        )
        SystemLoggerStore.get().debug(
            "Tagging LLM system prompt (document=%s):\n%s",
            str(document.relative_path).replace("%", "%%"),
            system_prompt.replace("%", "%%"),
        )

        user_content = document.markdown or document.text or ""

        messages: list[LLMChatMessage] = []
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
                content=[LLMChatMessageText(message=user_content)],
            )
        )

        request = LLMChatRequest(
            provider=provider,
            model=model,
            messages=messages,
            reasoning=reasoning,
            temperature=temperature,
            max_tokens=TAGGING_LLM_MAX_COMPLETION_TOKENS,
        )

        context.logger.info("Tagging: working on %s", document.relative_path)
        started_at = time.perf_counter()
        last_parsed: tuple[list[str], str | None, str | None] = ([], None, None)
        last_raw = ""
        user_len = len(user_content)

        llm = LLMProvider()

        for attempt in range(2):
            use_cache = attempt == 0
            try:
                response = llm.chat(request, cache=use_cache)
            except Exception as e:
                get_system_logger().warning(
                    "tagging_processing error source=%s: %s",
                    document.relative_path,
                    e,
                    exc_info=True,
                )
                return document

            if usage_acc is not None:
                if usage_lock is not None:
                    with usage_lock:
                        accumulate_llm_usage(usage_acc, response)
                else:
                    accumulate_llm_usage(usage_acc, response)

            if context.cancel_event is not None and context.cancel_event.is_set():
                return document

            text_parts: list[str] = []
            if response.message and response.message.content:
                for block in response.message.content:
                    if isinstance(block, LLMChatMessageText):
                        text_parts.append(block.message)
                    elif hasattr(block, "message") and isinstance(
                        getattr(block, "message"), str
                    ):
                        text_parts.append(block.message)
            raw_response = "\n".join(text_parts).strip() if text_parts else ""
            if not raw_response and getattr(response, "message_reasoning", None):
                raw_response = (response.message_reasoning or "").strip()
            last_raw = raw_response
            parsed = TaggingResultParser.parse_llm_response(raw_response, tag_format)
            last_parsed = parsed
            tags = parsed[0]
            if tags:
                elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                get_system_logger().info(
                    "tagging_processing done source=%s chars=%s elapsed_ms=%s attempts=%s",
                    document.relative_path,
                    user_len,
                    elapsed_ms,
                    attempt + 1,
                )
                return TaggingResultParser.merge_parsed_into_document(document, parsed)

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        frag = last_raw[:300] if len(last_raw) > 300 else last_raw
        get_system_logger().warning(
            "tagging_processing no_tags_after_retry source=%s chars=%s elapsed_ms=%s "
            "response_len=%s fragment=%s",
            document.relative_path,
            user_len,
            elapsed_ms,
            len(last_raw),
            frag,
        )
        return TaggingResultParser.merge_parsed_into_document(document, last_parsed)
