"""Tests for ProjectPipelineLogger: project file log and console sink."""

from __future__ import annotations

from pathlib import Path

from src.modules.project_pipeline.interfaces import ProjectPipelineLogger


def test_writes_to_project_file(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    logger = ProjectPipelineLogger(project_root)
    logger.info("pipeline message")
    project_log = project_root / "logs" / "pipeline.log"
    assert project_log.exists()
    assert "pipeline message" in project_log.read_text(encoding="utf-8")


def test_console_sink_receives_line(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    project_root.mkdir()
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    received: list[str] = []
    logger = ProjectPipelineLogger(project_root, console_sink=received.append)
    logger.warning("sink test")
    assert any("sink test" in line for line in received)
    assert any("[WARNING]" in line for line in received)
