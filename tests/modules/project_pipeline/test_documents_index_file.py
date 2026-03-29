"""Result index: DocumentsIndexFile."""

from src.modules.markdown.models import MarkdownDocument
from src.modules.project_pipeline.stages.result.documents_index_file import (
    DocumentsIndexFile,
    result_relative_md_path,
)


def test_result_relative_md_path() -> None:
    doc = MarkdownDocument("x/a.md", "a.md", "t", markdown="#")
    assert result_relative_md_path(doc) == "x/a.md"
    doc2 = MarkdownDocument("", "file.pdf", "t", markdown="#")
    assert result_relative_md_path(doc2) == "file.md"


def test_documents_index_file_render_structure() -> None:
    docs = [
        MarkdownDocument(
            "b.md",
            "b.md",
            "t",
            markdown="# B",
            name="Имя B",
            description="Описание B\nвторая строка",
            date="2025-01-01",
            tags=["tag_one", "Tag_two"],
        ),
        MarkdownDocument(
            "a.md",
            "a.md",
            "t",
            markdown="# A",
            name=None,
            description=None,
            date=None,
            tags=[],
        ),
    ]
    md = DocumentsIndexFile(docs).render()
    assert md.startswith("# Индекс документов")
    # Order by date (newer first): b.md with date, then a.md without date
    assert md.index("## [b.md]") < md.index("## [a.md]")
    assert "## [a.md]" in md
    assert "## [b.md]" in md
    assert "Описание B вторая строка" in md
    assert "Date: 2025-01-01" in md
    assert "Tags: tag_one, Tag_two" in md
    # a.md: empty description → Date / Tags follow immediately
    after_a = md.split("## [a.md]", 1)[1]
    if "##" in after_a:
        after_a = after_a.split("##", 1)[0]
    assert "\n\nDate: \nTags:" in after_a
