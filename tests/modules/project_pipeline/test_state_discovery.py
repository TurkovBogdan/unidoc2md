"""Tests for DiscoveryStage."""

from __future__ import annotations

from pathlib import Path

from src.modules.project.project_config import ProjectConfig
from src.modules.project_pipeline.models import PipelineContext
from src.modules.project_pipeline.stages import DiscoveryStage


def test_run_returns_documents_when_docs_exist(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.pdf").write_bytes(b"x")
    (docs / "b.pdf").write_bytes(b"y")
    config = ProjectConfig.create_default(tmp_path)
    logger_calls: list[tuple[str, tuple]] = []

    class MockLogger:
        def info(self, msg: str, *args: object) -> None:
            logger_calls.append(("info", (msg,) + args))

        def warning(self, msg: str, *args: object) -> None:
            logger_calls.append(("warning", (msg,) + args))

        def debug(self, msg: str, *args: object) -> None:
            logger_calls.append(("debug", (msg,) + args))

        def error(self, msg: str, *args: object) -> None:
            logger_calls.append(("error", (msg,) + args))

        def exception(self, msg: str, *args: object) -> None:
            logger_calls.append(("exception", (msg,) + args))

    context = PipelineContext(config=config, logger=MockLogger(), cancel_event=None)
    stage = DiscoveryStage()
    result = stage.run(context, None)

    assert result.success
    assert len(result.result) == 2
    assert result.payload == [2]

    def _render_info(args: tuple[object, ...]) -> str:
        msg, *rest = args
        m = str(msg)
        if rest and "%" in m:
            try:
                return m % tuple(rest)
            except (TypeError, ValueError):
                pass
        return f"{m} {' '.join(str(x) for x in rest)}" if rest else m

    info_texts = [_render_info(c[1]) for c in logger_calls if c[0] == "info"]
    assert any("Discovery: scanning" in t for t in info_texts)
    assert any("Discovery: found" in t and "2" in t for t in info_texts)


def test_run_returns_empty_and_warns_when_docs_missing(tmp_path: Path) -> None:
    config = ProjectConfig.create_default(tmp_path)
    assert not (tmp_path / "docs").exists()
    logger_calls: list[tuple[str, tuple]] = []

    class MockLogger:
        def info(self, msg: str, *args: object) -> None:
            logger_calls.append(("info", (msg,) + args))

        def warning(self, msg: str, *args: object) -> None:
            logger_calls.append(("warning", (msg,) + args))

        def debug(self, msg: str, *args: object) -> None:
            logger_calls.append(("debug", (msg,) + args))

        def error(self, msg: str, *args: object) -> None:
            logger_calls.append(("error", (msg,) + args))

        def exception(self, msg: str, *args: object) -> None:
            logger_calls.append(("exception", (msg,) + args))

    context = PipelineContext(config=config, logger=MockLogger(), cancel_event=None)
    stage = DiscoveryStage()
    result = stage.run(context, None)

    assert result.success
    assert result.result == []
    assert result.payload == [0]
    assert any(c[0] == "warning" for c in logger_calls)
    assert any(
        "not found" in str(c[1][0]).lower() for c in logger_calls if c[0] == "warning"
    )
