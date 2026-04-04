"""Tests for PipelineRunner."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from src.modules.file_discovery.models import DiscoveredDocument
from src.modules.file_extract import build_extract_config
from src.modules.file_extract.models import (
    ExtractedDocument,
    ExtractedDocumentContent,
    SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
    SEMANTIC_TYPE_REQUIRED_DETECTION,
)
from src.modules.project.project_config import ProjectConfig
from src.modules.project.sections.image_processing_config import ImageProcessingConfig
from src.modules.project.sections.pipeline_config import KEY_IMAGE_PROCESSING_THREADS
from src.modules.project_pipeline.pipeline_runner import PipelineRunner
from src.modules.project_pipeline.pipeline_state_storage import PipelineStateStorage


def test_run_returns_false_when_claim_fails() -> None:
    storage = PipelineStateStorage()
    storage.claim(Path("/other"))
    config = ProjectConfig.create_default(Path("/my/project"))
    runner = PipelineRunner(storage)
    result = runner.run(config)
    assert result is False


def test_run_returns_true_and_logs(tmp_path: Path) -> None:
    storage = PipelineStateStorage()
    config = ProjectConfig.create_default(tmp_path)
    sink_calls: list[str] = []
    runner = PipelineRunner(storage)

    result = runner.run(config, console_sink=sink_calls.append)

    assert result is True
    assert any("Project started" in s for s in sink_calls)
    assert any("Project finished" in s for s in sink_calls)


def test_run_respects_cancel(tmp_path: Path, monkeypatch) -> None:
    from src.modules.project_pipeline.stages import (
        BasePipelineStage,
        PipelineContext,
        StageResult,
    )

    storage = PipelineStateStorage()
    config = ProjectConfig.create_default(tmp_path)
    sink_calls: list[str] = []

    class BlockingStage(BasePipelineStage):
        @property
        def stage_id(self) -> str:
            return "blocking"

        def run(self, context: PipelineContext, input_result: object) -> StageResult:
            context.logger.info("Discovery: fake start")
            while context.cancel_event is not None and not context.cancel_event.is_set():
                time.sleep(0.01)
            return StageResult.ok([])

    monkeypatch.setattr(
        "src.modules.project_pipeline.pipeline_runner.PIPELINE_STAGES",
        [BlockingStage()],
    )
    runner = PipelineRunner(storage)

    def do_cancel() -> None:
        time.sleep(0.05)
        storage.request_cancel()

    threading.Thread(target=do_cancel, daemon=True).start()
    result = runner.run(config, console_sink=sink_calls.append)

    assert result is True
    assert any("Project started" in s for s in sink_calls)
    assert any("Project stopped" in s for s in sink_calls)


def test_start_run_calls_on_done_false_when_already_running(tmp_path: Path) -> None:
    storage = PipelineStateStorage()
    storage.claim(tmp_path)
    config = ProjectConfig.create_default(tmp_path)
    runner = PipelineRunner(storage)
    done_args: list[tuple[bool, str | None]] = []

    runner.start_run(
        config,
        on_done=lambda success, msg: done_args.append((success, msg)),
        console_sink=lambda s: None,
    )

    assert len(done_args) == 1
    assert done_args[0][0] is False
    assert "Another project is already running." in (done_args[0][1] or "")


def test_run_image_processing_stage_processes_each_image_item(
    tmp_path: Path, monkeypatch
) -> None:
    """ImageProcessingStage passes each image item to the worker and updates content."""
    from src.modules.project_pipeline.stages import (
        ImageProcessingStage,
        PipelineContext,
    )

    processed_paths: list[str | None] = []

    def fake_worker(item: ExtractedDocumentContent) -> ExtractedDocumentContent:
        processed_paths.append(str(item.path) if item.path is not None else None)
        return ExtractedDocumentContent(
            content_type="text",
            semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
            path=None,
            mime_type="text/plain",
            content_hash="ocr-hash",
            value=f"ocr:{item.path}",
        )

    def fake_run_parallel(*, task_items, worker, handle_result, **kwargs) -> None:
        for meta, item in task_items:
            result = fake_worker(item)
            handle_result(meta, result)

    monkeypatch.setattr(
        "src.modules.project_pipeline.stages.image_processing.stage.run_parallel_stage",
        fake_run_parallel,
    )
    config = ProjectConfig.create_default(tmp_path)
    config.image_processing["text_recognition"] = (
        ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.ocr
    )
    config.pipeline[KEY_IMAGE_PROCESSING_THREADS] = 2
    extract_config = build_extract_config(
        tmp_path, config.extract, config.paths.cache_extract
    )
    extracted = [
        ExtractedDocument(
            source=DiscoveredDocument(
                path=str(tmp_path / "doc1.pdf"),
                folder=".",
                filename="doc1.pdf",
                extension=".pdf",
                mime_type="application/pdf",
                hash="hash1",
            ),
            config=extract_config,
            extract_hash="extract1",
            content=[
                ExtractedDocumentContent(
                    content_type="image",
                    semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
                    path=tmp_path / "a.png",
                    mime_type="image/png",
                ),
                ExtractedDocumentContent(
                    content_type="image",
                    semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
                    path=tmp_path / "b.png",
                    mime_type="image/png",
                ),
                ExtractedDocumentContent(
                    content_type="text",
                    semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
                    path=None,
                    mime_type="text/plain",
                    value="keep",
                ),
            ],
        ),
        ExtractedDocument(
            source=DiscoveredDocument(
                path=str(tmp_path / "doc2.pdf"),
                folder=".",
                filename="doc2.pdf",
                extension=".pdf",
                mime_type="application/pdf",
                hash="hash2",
            ),
            config=extract_config,
            extract_hash="extract2",
            content=[
                ExtractedDocumentContent(
                    content_type="image",
                    semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
                    path=tmp_path / "c.png",
                    mime_type="image/png",
                ),
                ExtractedDocumentContent(
                    content_type="image",
                    semantic_type=SEMANTIC_TYPE_REQUIRED_DETECTION,
                    path=tmp_path / "d.png",
                    mime_type="image/png",
                ),
            ],
        ),
    ]
    sink_calls: list[str] = []
    logger = _FakeLogger(sink_calls.append)
    context = PipelineContext(config=config, logger=logger, cancel_event=None)
    stage = ImageProcessingStage()
    result = stage.run(context, extracted)
    assert result.success
    assert len(processed_paths) == 4
    out = result.result
    assert all(d is not None for d in out)
    assert out[0].content[0].content_type == "text"
    assert out[0].content[1].content_type == "text"
    assert out[0].content[2].value == "keep"
    assert out[1].content[0].content_type == "text"
    assert out[1].content[1].content_type == "text"
    assert any("queue 4 images" in line for line in sink_calls)
    assert any("logic=ocr" in line for line in sink_calls)
    assert result.payload and isinstance(result.payload[0], dict)
    assert result.payload[0].get("logic") == "ocr"
    ocr_vis = result.payload[0].get("vision")
    assert isinstance(ocr_vis, dict)
    assert ocr_vis.get("billing") == "ocr"
    assert ocr_vis.get("api_calls") == 0
    assert ocr_vis.get("cache_hits") == 0


def test_image_processing_stage_uses_worker_limit_from_config(tmp_path: Path) -> None:
    """ImageProcessingStage with OCR mode returns get_max_workers=1."""
    from src.modules.project_pipeline.stages import ImageProcessingStage

    config = ProjectConfig.create_default(tmp_path)
    config.image_processing["text_recognition"] = (
        ImageProcessingConfig.IMAGE_PROCESSING_LOGICS.ocr
    )
    stage = ImageProcessingStage()
    assert stage._get_max_workers(config) == 1


def test_extract_stage_excludes_skip_algorithm_files(
    tmp_path: Path, monkeypatch
) -> None:
    """ExtractStage excludes algorithm=skip files before parallel processing."""
    from src.modules.file_extract.models import (
        ExtractedDocument,
        ExtractedDocumentContent,
    )
    from src.modules.file_extract.models import SEMANTIC_TYPE_DOCUMENT_FRAGMENT
    from src.modules.project_pipeline.stages import (
        ExtractStage,
        PipelineContext,
    )

    config = ProjectConfig.create_default(tmp_path)
    config.extract["pdf_extract_provider"] = {"algorithm": "skip"}
    config.extract["text_extract_provider"] = {"algorithm": "process"}
    discovered = [
        DiscoveredDocument(
            path=str(tmp_path / "doc.pdf"),
            folder=".",
            filename="doc",
            extension=".pdf",
            mime_type="application/pdf",
            hash=None,
        ),
        DiscoveredDocument(
            path=str(tmp_path / "readme.txt"),
            folder=".",
            filename="readme",
            extension=".txt",
            mime_type="text/plain",
            hash=None,
        ),
    ]
    sink_calls: list[str] = []

    def fake_run_parallel(**kwargs) -> None:
        task_items = kwargs.get("task_items", [])
        extract_config = build_extract_config(
            tmp_path, config.extract, config.paths.cache_extract
        )
        for (index, doc), _ in task_items:
            kwargs["handle_result"](
                (index, doc),
                ExtractedDocument(
                    source=doc,
                    config=extract_config,
                    extract_hash="fake",
                    content=[
                        ExtractedDocumentContent(
                            content_type="text",
                            semantic_type=SEMANTIC_TYPE_DOCUMENT_FRAGMENT,
                            path=None,
                            mime_type="text/plain",
                            value="",
                        )
                    ],
                ),
            )

    monkeypatch.setattr(
        "src.modules.project_pipeline.stages.extract.stage.run_parallel_stage",
        fake_run_parallel,
    )
    context = PipelineContext(
        config=config, logger=_FakeLogger(sink_calls.append), cancel_event=None
    )
    stage = ExtractStage()
    result = stage.run(context, discovered)
    assert result.success
    assert len(result.result) == 1
    assert result.payload == [1, 1, 1, 0, 0]
    assert any('skipped 1 files' in s for s in sink_calls)


def test_run_fail_fast_on_stage_error(tmp_path: Path, monkeypatch) -> None:
    """When a stage returns result.success=False, run aborts, re-raises, and storage is cleared."""
    from src.modules.project_pipeline.stages import (
        BasePipelineStage,
        PipelineContext,
        StageResult,
    )

    storage = PipelineStateStorage()
    config = ProjectConfig.create_default(tmp_path)

    class FailingStage(BasePipelineStage):
        @property
        def stage_id(self) -> str:
            return "failing"

        def run(self, context: PipelineContext, input_result: object) -> StageResult:
            return StageResult.fail([], error=ValueError("stage error"))

    monkeypatch.setattr(
        "src.modules.project_pipeline.pipeline_runner.PIPELINE_STAGES",
        [FailingStage()],
    )
    runner = PipelineRunner(storage)
    with pytest.raises(ValueError, match="stage error"):
        runner.run(config)
    assert storage.get_current() is None


def test_pipeline_stages_returns_six_stages() -> None:
    """Stage order: discovery -> extract -> image_processing -> markdown -> tagging -> result."""
    from src.modules.project_pipeline.pipeline_runner import PIPELINE_STAGES

    assert len(PIPELINE_STAGES) == 6
    assert type(PIPELINE_STAGES[0]).__name__ == "DiscoveryStage"
    assert type(PIPELINE_STAGES[1]).__name__ == "ExtractStage"
    assert type(PIPELINE_STAGES[2]).__name__ == "ImageProcessingStage"
    assert type(PIPELINE_STAGES[3]).__name__ == "MarkdownStage"
    assert type(PIPELINE_STAGES[4]).__name__ == "TaggingStage"
    assert type(PIPELINE_STAGES[5]).__name__ == "ResultStage"


class _FakeLogger:
    def __init__(self, sink) -> None:
        self._sink = sink

    def info(self, msg, *args, **kwargs) -> None:
        text = str(msg) % args if args else str(msg)
        self._sink(text)
