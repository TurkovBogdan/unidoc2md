"""Central markdown normalization: tables and other steps."""

from __future__ import annotations

import yaml

from .yaml_frontmatter import clear_markdown_yaml, extract_markdown_yaml


def _clean_yaml_value(value: object) -> object | None:
    """Recursively drop empty values from a YAML-shaped structure."""
    if value is None:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    if isinstance(value, list):
        cleaned_list: list[object] = []
        for item in value:
            cleaned_item = _clean_yaml_value(item)
            if cleaned_item is not None:
                cleaned_list.append(cleaned_item)
        return cleaned_list or None
    if isinstance(value, dict):
        cleaned_dict: dict[object, object] = {}
        for key, item in value.items():
            cleaned_item = _clean_yaml_value(item)
            if cleaned_item is not None:
                cleaned_dict[key] = cleaned_item
        return cleaned_dict or None
    return value


def normalize_markdown_yaml(text: str) -> str:
    """
    Normalize YAML front matter: remove empty fields.
    ``tags`` values are not rewritten (casing and string form stay as in the source).

    If no fields remain after cleanup, the front matter block is removed entirely.
    """
    if not text:
        return text
    yaml_data = extract_markdown_yaml(text)
    if yaml_data is None:
        return text
    cleaned = _clean_yaml_value(yaml_data)
    body = clear_markdown_yaml(text).lstrip("\n")
    if not isinstance(cleaned, dict) or not cleaned:
        return body
    yaml_block = yaml.safe_dump(
        cleaned,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"---\n{yaml_block}\n---\n\n{body}"


def _is_table_row(line: str) -> bool:
    """True if the line starts with ``|`` and contains at least one more ``|``."""
    stripped = line.strip()
    return bool(stripped) and stripped.startswith("|") and "|" in stripped[1:]


def _normalize_table_line(line: str) -> str:
    """
    Normalize one table row: single spaces around each ``|``.
    Example: ``|a|b|c|`` -> ``| a | b | c |``
    """
    parts = line.split("|")
    if len(parts) < 2:
        return line
    cells = [p.strip() for p in parts[1:-1]]
    return "| " + " | ".join(cells).rstrip() + " |"


def normalize_markdown_tables(text: str) -> str:
    """
    Normalize all markdown tables: one space before and after each ``|``
    (header, separator, and body rows).

    :param text: Source markdown.
    :return: Text with normalized tables.
    """
    if not text:
        return text
    lines = text.split("\n")
    result: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _is_table_row(line):
            result.append(line)
            i += 1
            continue
        table_lines: list[str] = []
        while i < len(lines) and _is_table_row(lines[i]):
            table_lines.append(lines[i])
            i += 1
        for tline in table_lines:
            result.append(_normalize_table_line(tline))
    return "\n".join(result)


def normalize_markdown(text: str) -> str:
    """
    Main markdown normalization entry point.
    Applies YAML cleanup and table normalization in sequence.

    :param text: Source markdown.
    :return: Normalized text.
    """
    if not text:
        return text
    result = normalize_markdown_yaml(text)
    result = normalize_markdown_tables(result)
    return result
