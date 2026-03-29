"""YAML frontmatter extraction from markdown text and building markdown from the model."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from src.modules.markdown.models import MarkdownDocument


def extract_markdown_yaml(text: str) -> dict | None:
    """
    Extract YAML front matter from the start of the text (``---\\n...\\n---``).

    :param text: Source text (markdown with optional front matter).
    :return: Parameter dict if present; empty dict if the block exists but is empty;
             None if there is no block or it is invalid.
    """
    if not text or not text.strip():
        return None
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return None
    rest = stripped[3:].lstrip("\n")
    if rest.startswith("---"):
        return {}
    end = rest.find("\n---")
    if end == -1:
        return None
    yaml_block = rest[:end].strip()
    if not yaml_block:
        return {}
    try:
        data = yaml.safe_load(yaml_block)
    except yaml.YAMLError:
        return None
    if data is None:
        return {}
    if not isinstance(data, dict):
        return None
    return data


def _frontmatter_tail(text: str) -> tuple[str, str] | None:
    """
    If ``text`` starts with front matter (``---\\n...\\n---``), return ``(leading_ws, body)``.
    Otherwise None.
    """
    if not text or not text.strip():
        return None
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return None
    prefix_ws = text[: len(text) - len(stripped)]
    rest = stripped[3:].lstrip("\n")
    if rest.startswith("---"):
        return (prefix_ws, rest[3:].lstrip("\n"))
    end = rest.find("\n---")
    if end == -1:
        return None
    body = rest[end + 4 :].lstrip("\n")  # after "\n---"
    return (prefix_ws, body)


def clear_markdown_yaml(text: str) -> str:
    """
    Remove YAML front matter from the start of the text (``---\\n...\\n---`` block).

    :param text: Source text (markdown with optional front matter).
    :return: Text without the front matter block; unchanged if there is no block.
    """
    pair = _frontmatter_tail(text)
    if pair is None:
        return text
    return pair[0] + pair[1]


def build_markdown_from_document(doc: MarkdownDocument) -> str:
    """
    Build final markdown from model fields: front matter (name, description, date, tags) + body.
    """
    body = clear_markdown_yaml(doc.markdown or "").lstrip("\n")
    front: dict[str, object] = {}
    if doc.name:
        front["name"] = doc.name
    if doc.description:
        front["description"] = doc.description
    if doc.date:
        front["date"] = doc.date
    if doc.tags:
        front["tags"] = doc.tags
    if not front:
        return doc.markdown or ""
    yaml_block = yaml.safe_dump(
        front,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"---\n{yaml_block}\n---\n\n{body}"
