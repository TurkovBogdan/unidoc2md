"""Tests for extract_markdown_yaml."""

from __future__ import annotations

import pytest

from src.modules.markdown.utils import clear_markdown_yaml, extract_markdown_yaml


def test_no_frontmatter_returns_none() -> None:
    assert extract_markdown_yaml("") is None
    assert extract_markdown_yaml("  ") is None
    assert extract_markdown_yaml("# Title\nbody") is None
    assert extract_markdown_yaml("---\nno closing") is None


def test_empty_frontmatter_returns_empty_dict() -> None:
    assert extract_markdown_yaml("---\n---\n# Doc") == {}
    assert extract_markdown_yaml("---\n\n---\nbody") == {}


def test_valid_frontmatter_returns_dict() -> None:
    text = "---\ntitle: Hello\ndescription: World\n---\n# Content"
    assert extract_markdown_yaml(text) == {"title": "Hello", "description": "World"}


def test_leading_whitespace_then_frontmatter() -> None:
    text = "  \n---\ntag: x\n---\nbody"
    assert extract_markdown_yaml(text) == {"tag": "x"}


def test_multiline_frontmatter_with_list_and_unicode() -> None:
    text = """---
tags:
  - Стандарт
  - Python
description: Обеспечивает отложенное вычисление аннотаций — позволяет использовать forward references без кавычек. Короткие, на английском. Комментируем неочевидные решения, не пересказываем код.
---

## Именование
Используем подход самодокументирующихся имён — код должен читаться как текст без дополнительных пояснений. Названия переменных, функций и классов явно отражают их назначение.
"""
    result = extract_markdown_yaml(text)
    assert result is not None
    assert result["tags"] == ["Стандарт", "Python"]
    assert "Обеспечивает отложенное вычисление" in result["description"]
    assert "forward references" in result["description"]


def test_clear_markdown_yaml_no_frontmatter_unchanged() -> None:
    raw = "# Title\nbody"
    assert clear_markdown_yaml(raw) == raw


def test_clear_markdown_yaml_removes_frontmatter() -> None:
    text = "---\ntitle: Hi\n---\n# Doc\nbody"
    assert clear_markdown_yaml(text) == "# Doc\nbody"


def test_clear_markdown_yaml_empty_frontmatter() -> None:
    text = "---\n---\n# Doc"
    assert clear_markdown_yaml(text) == "# Doc"


def test_clear_markdown_yaml_multiline_preserves_body() -> None:
    text = """---
tags:
  - A
description: D
---

## Именование
Текст после разметки.
"""
    result = clear_markdown_yaml(text)
    assert "## Именование" in result
    assert "Текст после разметки" in result
    assert "tags:" not in result
    assert "---" not in result or result.strip().startswith("##")
