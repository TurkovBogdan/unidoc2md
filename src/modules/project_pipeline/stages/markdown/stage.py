"""Этап markdown: сбор текста и опциональная LLM-обработка."""

from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Any

from src.modules.file_extract.models import (
    CONTENT_TYPE_MARKDOWN,
    CONTENT_TYPE_TEXT,
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_MARKDOWN,
)
from src.modules.markdown.models import MarkdownDocument
from src.modules.markdown.utils import clear_markdown_yaml, extract_markdown_yaml
from src.modules.project.sections.markdown_config import MarkdownConfig
from src.modules.project.sections.pipeline_config import (
    KEY_MARKDOWN_THREADS,
    MARKDOWN_THREADS_DEFAULT,
    MARKDOWN_THREADS_MAX,
    MARKDOWN_THREADS_MIN,
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
from ..parallel import run_parallel_stage

# Между текстовыми фрагментами (и между фрагментом и маркером MD) в user-сообщении для LLM.
LLM_USER_FRAGMENT_SEPARATOR = "\n"

# Системный промпт этапа: инструкции для создания разметки. Дополнительные инструкции из конфига (llm_system_prompt) добавляются после.
MARKDOWN_LLM_SYSTEM_PROMPT = """You are an expert Markdown formatter. Your ONLY task is to take the provided raw text and convert it into clean, well-structured Markdown.

## Core rules you MUST follow:
- Preserve the original language exactly as provided. NEVER translate anything.
- Do NOT rewrite, summarize, paraphrase, or change the meaning of the text.
- You MAY correct obvious typos or spelling mistakes only if they are clearly unintentional.

## Formatting rules:
- Detect the logical structure of the text and format it using Markdown.
* Preserve the original structure as much as possible.

### Allowed Markdown formatting:
* `##`, `###` for headings and subheadings when appropriate
* blank lines between logical sections
* `-` for bullet lists
* numbered lists for ordered lists
* `> ` for quotes
* **bold** and *italic* if clearly implied by the structure
* Markdown tables when tabular data is detected

### Table rules (STRICT):
If the content represents a table, you MUST format it as a standard Markdown table with aligned separators and at least three dashes per column.

Example format:
| Column A | Column B |
| --- | --- |
| Value 1 | Value 2 |
"""


def _compose_markdown_llm_system_prompt(user_instructions: str | None) -> str:
    """
    Системное сообщение для LLM: константа этапа + при необходимости доп. инструкции из конфига (llm_system_prompt).
    """
    base = (MARKDOWN_LLM_SYSTEM_PROMPT or "").strip()
    add_raw = (user_instructions or "").strip() if isinstance(user_instructions, str) else ""
    if not add_raw:
        return base
    return f"{base}\n\n{add_raw}"


def _iter_pipeline_markdown_segments(
    content: list[ExtractedDocumentContent],
) -> list[tuple[str, str]]:
    """
    Порядок фрагментов для сборки markdown: только text и markdown-носители.
    Картинки и прочее пропускаются. Markdown-фрагменты (content_type / semantic_type)
    не должны попадать в LLM как сырой текст — только в итоговое тело.
    """
    segments: list[tuple[str, str]] = []
    for item in content:
        val = getattr(item, "value", None)
        if val is None:
            continue
        if item.content_type == CONTENT_TYPE_TEXT and (
            item.semantic_type != SEMANTIC_TYPE_MARKDOWN
        ):
            segments.append(("text", clear_markdown_yaml(str(val))))
            continue
        if item.content_type == CONTENT_TYPE_MARKDOWN:
            segments.append(("markdown", str(val)))
            continue
        if item.semantic_type == SEMANTIC_TYPE_MARKDOWN:
            segments.append(("markdown", str(val)))
    return segments


def _join_segment_bodies(
    segments: tuple[tuple[str, str], ...],
    *,
    kinds: set[str],
    sep: str = "\n\n",
) -> str:
    parts = [body for k, body in segments if k in kinds]
    return sep.join(parts) if parts else ""


def _build_llm_user_body_with_markdown_placeholders(
    segments: tuple[tuple[str, str], ...],
) -> tuple[str, dict[str, str]]:
    """Текст для LLM: markdown-куски заменены на уникальные маркеры (модель должна их сохранить)."""
    token_to_body: dict[str, str] = {}
    parts: list[str] = []
    for kind, body in segments:
        if kind == "text":
            parts.append(body)
        else:
            tok = f"[[UNIDOC_MD:{uuid.uuid4().hex}]]"
            token_to_body[tok] = body
            parts.append(tok)
    return LLM_USER_FRAGMENT_SEPARATOR.join(parts), token_to_body


def _restore_markdown_placeholders(llm_text: str, token_to_body: dict[str, str]) -> str:
    out = llm_text
    missing: list[str] = []
    for tok, body in token_to_body.items():
        if tok in out:
            out = out.replace(tok, body)
        else:
            missing.append(body)
    if missing:
        out = out.rstrip() + "\n\n" + "\n\n".join(missing)
    return out


class MarkdownStage(BasePipelineStage):
    """Генерация markdown из извлечённых документов; опционально LLM-обработка."""

    _markdown_usage_state: tuple[threading.Lock, LLMUsageAcc] | None = None

    @property
    def stage_id(self) -> str:
        return "markdown"

    def is_enabled(self, context: PipelineContext) -> bool:
        """Этап всегда включён: нужен для преобразования ExtractedDocument -> MarkdownDocument."""
        return True

    def _is_llm_enabled(self, context: PipelineContext) -> bool:
        return self._get_logic(context.config) == MarkdownConfig.MARKDOWN_LOGICS.llm_processing

    def run(self, context: PipelineContext, input_result: object) -> StageResult:
        documents: list[ExtractedDocument | None] = (
            input_result if isinstance(input_result, list) else []
        )
        threads = self._get_max_workers(context.config)
        logic = self._get_logic(context.config)
        context.logger.info(
            "Markdown: stage start, logic=%s, workers=%s", logic, threads
        )
        markdown_list: list[MarkdownDocument] = []
        task_items: list[tuple[tuple[int, str], MarkdownDocument]] = []
        for document in documents:
            if document is None:
                continue
            if context.cancel_event is not None and context.cancel_event.is_set():
                break
            md_doc = self._extracted_to_markdown(context.config, document)
            list_index = len(markdown_list)
            markdown_list.append(md_doc)
            task_items.append(((list_index, document.source.filename), md_doc))
        if not self._is_llm_enabled(context):
            context.logger.info(
                "Markdown: LLM processing disabled, prepared %s documents",
                len(markdown_list),
            )
            return StageResult.ok(
                markdown_list,
                payload=[self._markdown_summary_payload("none", "", "", None, None, empty_llm_usage_acc())],
            )

        section = context.config.markdown or {}
        K = MarkdownConfig.MARKDOWN_KEYS
        provider = (section.get(K.llm_provider) or "").strip()
        model = (section.get(K.llm_model) or "").strip()
        price_in, price_out = resolve_llm_registry_prices(provider, model)
        context.logger.info(
            "Markdown: LLM provider=%s, model=%s, input price per 1M=%s, output price per 1M=%s",
            provider or "—",
            model or "—",
            price_in if price_in is not None else "—",
            price_out if price_out is not None else "—",
        )

        usage_lock = threading.Lock()
        usage_acc: LLMUsageAcc = empty_llm_usage_acc()
        self._markdown_usage_state = (usage_lock, usage_acc)

        def _payload_snap() -> dict[str, Any]:
            with usage_lock:
                snap: LLMUsageAcc = {
                    "prompt": usage_acc["prompt"],
                    "reasoning": usage_acc["reasoning"],
                    "completion": usage_acc["completion"],
                    "total": usage_acc["total"],
                    "cache_hits": usage_acc["cache_hits"],
                    "api_calls": usage_acc["api_calls"],
                }
            return self._markdown_summary_payload(
                MarkdownConfig.MARKDOWN_LOGICS.llm_processing,
                provider,
                model,
                price_in,
                price_out,
                snap,
            )

        def _emit_progress(documents_done: int, documents_total: int) -> None:
            self._emit_markdown_progress(
                context,
                provider=provider,
                model=model,
                price_in=price_in,
                price_out=price_out,
                usage_lock=usage_lock,
                usage_acc=usage_acc,
                documents_done=documents_done,
                documents_total=documents_total,
            )

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
                def process_one(doc: MarkdownDocument) -> MarkdownDocument:
                    return self._execute_item(context, doc)

                def handle_result(
                    meta: tuple[int, str], result: MarkdownDocument
                ) -> None:
                    target_index, _ = meta
                    if 0 <= target_index < len(markdown_list):
                        markdown_list[target_index] = result

                submitted = len(task_items)
                if submitted == 0:
                    context.logger.info("Markdown: no documents for LLM")
                    return StageResult.ok(
                        markdown_list, payload=[_payload_snap()]
                    )

                _emit_progress(0, submitted)

                run_parallel_stage(
                    stage_name="Markdown",
                    logger=context.logger,
                    task_items=task_items,
                    max_workers=threads,
                    cancel_event=context.cancel_event,
                    worker=process_one,
                    handle_result=handle_result,
                    describe_item=lambda meta: meta[1],
                    on_progress=lambda done, tot: _emit_progress(done, tot),
                )
            finally:
                llm_providers_set_cache_path(prev_cache)
        except ImportError:
            raise
        finally:
            self._markdown_usage_state = None

        context.logger.info(
            "Markdown: processed %s documents", len(markdown_list)
        )
        return StageResult.ok(markdown_list, payload=[_payload_snap()])

    @staticmethod
    def _markdown_summary_payload(
        logic: str,
        provider: str,
        model: str,
        price_input_per_million: float | None,
        price_output_per_million: float | None,
        usage_acc: LLMUsageAcc,
    ) -> dict[str, Any]:
        if logic != MarkdownConfig.MARKDOWN_LOGICS.llm_processing:
            return {"logic": logic, "llm": None}
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
        return {"logic": logic, "llm": llm_block}

    def _emit_markdown_progress(
        self,
        context: PipelineContext,
        *,
        provider: str,
        model: str,
        price_in: float | None,
        price_out: float | None,
        usage_lock: threading.Lock,
        usage_acc: LLMUsageAcc,
        documents_done: int,
        documents_total: int,
    ) -> None:
        sink = context.progress_sink
        if sink is None:
            return
        with usage_lock:
            snap: LLMUsageAcc = {
                "prompt": usage_acc["prompt"],
                "reasoning": usage_acc["reasoning"],
                "completion": usage_acc["completion"],
                "total": usage_acc["total"],
                "cache_hits": usage_acc["cache_hits"],
                "api_calls": usage_acc["api_calls"],
            }
        summary = self._markdown_summary_payload(
            MarkdownConfig.MARKDOWN_LOGICS.llm_processing,
            provider,
            model,
            price_in,
            price_out,
            snap,
        )
        envelope: dict[str, Any] = {
            **summary,
            "documents_done": documents_done,
            "documents_total": documents_total,
        }
        sink("markdown", envelope)

    def _get_logic(self, config: Any) -> str:
        section = config.markdown or {}
        logic = (
            section.get(MarkdownConfig.MARKDOWN_KEYS.markdown_logic)
            or MarkdownConfig.MARKDOWN_LOGICS.none
        )
        return str(logic).strip().lower()

    def _get_max_workers(self, config: Any) -> int:
        threads = config.pipeline.get(
            KEY_MARKDOWN_THREADS, MARKDOWN_THREADS_DEFAULT
        )
        try:
            threads = int(threads)
        except (TypeError, ValueError):
            threads = MARKDOWN_THREADS_DEFAULT
        return max(MARKDOWN_THREADS_MIN, min(MARKDOWN_THREADS_MAX, threads))

    def _extracted_to_markdown(
        self, config: Any, document: ExtractedDocument
    ) -> MarkdownDocument:
        segs = _iter_pipeline_markdown_segments(document.content)
        segment_runs = tuple(segs)
        full_body = "\n\n".join(body for _, body in segs) if segs else ""
        text_only = _join_segment_bodies(
            segment_runs,
            kinds={"text"},
            sep=LLM_USER_FRAGMENT_SEPARATOR,
        )
        folder = document.source.folder or ""
        if folder and folder != ".":
            rel_path = (
                f"{folder}/{document.source.filename}.md".replace("\\", "/")
            )
        else:
            rel_path = f"{document.source.filename}.md"
        if not folder or folder == ".":
            try:
                src_path = Path(document.source.path).resolve()
                docs_dir = config.paths.docs.resolve()
                rel_path = (
                    str(src_path.relative_to(docs_dir).with_suffix(".md"))
                    .replace("\\", "/")
                )
            except (ValueError, OSError, TypeError, AttributeError):
                pass
        md_doc = MarkdownDocument(
            relative_path=rel_path,
            filename=document.source.filename,
            text=text_only,
            markdown=full_body,
            segment_runs=segment_runs,
        )
        return self._enrich_metadata(md_doc)

    @staticmethod
    def _parse_yaml_tags(raw: object) -> list[str] | None:
        """Извлекает список тегов из значения YAML (список или строка). None если поля нет."""
        if raw is None:
            return None
        if isinstance(raw, str):
            part = raw.strip()
            return [part] if part else []
        if isinstance(raw, list):
            out: list[str] = []
            for item in raw:
                s = str(item).strip() if item is not None else ""
                if s:
                    out.append(s)
            return out
        return None

    def _enrich_metadata(self, document: MarkdownDocument) -> MarkdownDocument:
        yaml_data = extract_markdown_yaml(document.markdown or "")
        if not isinstance(yaml_data, dict):
            return document
        name = yaml_data.get("name")
        description = yaml_data.get("description")
        if description in (None, ""):
            description = yaml_data.get("summary")
        date = yaml_data.get("date")
        tags = self._parse_yaml_tags(yaml_data.get("tags"))
        if tags is None:
            tags = document.tags
        return MarkdownDocument(
            relative_path=document.relative_path,
            filename=document.filename,
            text=document.text,
            markdown=document.markdown,
            name=(
                str(name).strip()
                if name is not None and str(name).strip()
                else None
            ),
            description=(
                str(description).strip()
                if description is not None and str(description).strip()
                else None
            ),
            date=(
                str(date).strip()
                if date is not None and str(date).strip()
                else None
            ),
            tags=tags,
            segment_runs=document.segment_runs,
        )

    def _execute_item(
        self, context: PipelineContext, item: MarkdownDocument
    ) -> MarkdownDocument:
        if context.cancel_event is not None and context.cancel_event.is_set():
            return item
        if not self._is_llm_enabled(context):
            return self._enrich_metadata(item)
        return self._llm_processing(context, item)

    def _llm_processing(
        self, context: PipelineContext, document: MarkdownDocument
    ) -> MarkdownDocument:
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
        section = context.config.markdown or {}
        K = MarkdownConfig.MARKDOWN_KEYS
        provider = (section.get(K.llm_provider) or "").strip()
        model = (section.get(K.llm_model) or "").strip()
        if not provider or not model:
            return document
        segs = document.segment_runs
        token_to_body: dict[str, str] = {}
        if not segs:
            user_body = document.text or ""
        else:
            if not any(kind == "text" for kind, _ in segs):
                return self._enrich_metadata(document)
            user_body, token_to_body = _build_llm_user_body_with_markdown_placeholders(
                segs
            )
        reason_raw = (
            section.get(K.llm_reasoning)
            or MarkdownConfig.MARKDOWN_DEFAULTS.llm_reasoning
        ).strip().lower()
        try:
            reasoning = LLMChatReasoningEffort(reason_raw)
        except ValueError:
            reasoning = LLMChatReasoningEffort.DISABLED
        t = section.get(K.llm_temperature)
        temperature = MarkdownConfig.MARKDOWN_DEFAULTS.llm_temperature
        if t is not None:
            try:
                temperature = max(0.0, min(2.0, float(t)))
            except (TypeError, ValueError):
                pass
        user_instructions = (
            section.get(K.llm_system_prompt) or MarkdownConfig.MARKDOWN_DEFAULTS.llm_system_prompt
        ) or ""
        system_prompt = _compose_markdown_llm_system_prompt(user_instructions)
        if token_to_body:
            preserve = (
                "\n\nImportant: keep every [[UNIDOC_MD:...]] marker in your response unchanged "
                "(exact same strings); they will be replaced with markdown blocks."
            )
            system_prompt = (system_prompt + preserve).strip()
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
                content=[LLMChatMessageText(message=user_body)],
            )
        )
        request = LLMChatRequest(
            provider=provider,
            model=model,
            messages=messages,
            reasoning=reasoning,
            temperature=temperature,
            max_tokens=32768,
        )
        started_at = time.perf_counter()
        try:
            llm = LLMProvider()
            response = llm.chat(request, cache=True)
        except Exception as e:
            from src.core.logger import get_system_logger

            get_system_logger().warning(
                "markdown_processing error source=%s: %s",
                document.relative_path,
                e,
                exc_info=True,
            )
            raise
        usage_state = self._markdown_usage_state
        if usage_state is not None:
            lock, acc = usage_state
            with lock:
                accumulate_llm_usage(acc, response)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        from src.core.logger import get_system_logger

        get_system_logger().info(
            "markdown_processing done source=%s chars=%s elapsed_ms=%s",
            document.relative_path,
            len(document.text or ""),
            elapsed_ms,
        )
        if context.cancel_event is not None and context.cancel_event.is_set():
            return document
        text_parts: list[str] = []
        if response.message and response.message.content:
            for block in response.message.content:
                if isinstance(block, LLMChatMessageText):
                    text_parts.append(block.message)
        llm_raw = "\n".join(text_parts).strip()
        if token_to_body:
            base = llm_raw if llm_raw else user_body
            markdown_text = _restore_markdown_placeholders(base, token_to_body)
        else:
            markdown_text = llm_raw if llm_raw else (document.text or "")
        next_doc = MarkdownDocument(
            relative_path=document.relative_path,
            filename=document.filename,
            text=document.text,
            markdown=markdown_text,
            tags=document.tags,
            segment_runs=document.segment_runs,
        )
        return self._enrich_metadata(next_doc)
