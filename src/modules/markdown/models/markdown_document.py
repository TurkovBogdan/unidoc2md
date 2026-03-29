"""Markdown-stage result model: file path, raw text, markdown body, and YAML metadata."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MarkdownDocument:
    """Document after the markdown stage: relative path, name, markdown body, and metadata."""

    relative_path: str
    filename: str
    text: str
    markdown: str = ""
    name: str | None = None
    description: str | None = None
    date: str | None = None
    tags: list[str] = field(default_factory=list)
    #: Order of fragments from extract: ("text"|"markdown", body). Markdown segments are not sent to the LLM as raw text.
    segment_runs: tuple[tuple[str, str], ...] = field(default_factory=tuple)
