from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from ....models import ExtractedDocumentContent
from ....services.file_extract_cache import FileExtractCacheService
from .image_pipeline import OfficeImagePipeline

_DOCX_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "v": "urn:schemas-microsoft-com:vml",
}


def extract_docx(
    path: Path,
    storage: FileExtractCacheService,
    pipeline: OfficeImagePipeline,
    out: list[ExtractedDocumentContent],
    flush_text,
) -> None:
    rels, media_bytes = _docx_relationships_and_media(path)
    text_buffer: list[str] = []
    text_index = 0
    stem = pipeline.stem

    for token_type, value in _iter_docx_tokens(path):
        if token_type == "text":
            text_buffer.append(value)
            continue
        text_index = flush_text(text_buffer, stem, text_index, storage, out)
        target = rels.get(value)
        if not target:
            continue
        blob = media_bytes.get(target)
        if not blob:
            continue
        source_ext = Path(target).suffix.lower() or ".bin"
        item = pipeline.save(blob, source_ext)
        if item is not None:
            out.append(item)
    flush_text(text_buffer, stem, text_index, storage, out)


def _docx_relationships_and_media(path: Path) -> tuple[dict[str, str], dict[str, bytes]]:
    rels: dict[str, str] = {}
    media: dict[str, bytes] = {}
    with ZipFile(path) as zf:
        rels_xml_path = "word/_rels/document.xml.rels"
        if rels_xml_path in zf.namelist():
            rels_root = ET.fromstring(zf.read(rels_xml_path))
            for rel in rels_root.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                rid = rel.attrib.get("Id")
                target = rel.attrib.get("Target", "")
                if not rid or not target:
                    continue
                normalized = target.lstrip("/") if target.startswith("/") else str((Path("word") / target).as_posix())
                rels[rid] = normalized
        for name in zf.namelist():
            if name.startswith("word/media/"):
                media[name] = zf.read(name)
    return rels, media


def _iter_docx_tokens(path: Path) -> list[tuple[str, str]]:
    with ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    result: list[tuple[str, str]] = []
    for node in root.iter():
        tag = node.tag
        if tag == f"{{{_DOCX_NS['w']}}}t":
            value = node.text or ""
            if value:
                result.append(("text", value))
        elif tag == f"{{{_DOCX_NS['w']}}}tab":
            result.append(("text", "\t"))
        elif tag in (f"{{{_DOCX_NS['w']}}}br", f"{{{_DOCX_NS['w']}}}cr"):
            result.append(("text", "\n"))
        elif tag == f"{{{_DOCX_NS['a']}}}blip":
            rid = node.attrib.get(f"{{{_DOCX_NS['r']}}}embed") or node.attrib.get(f"{{{_DOCX_NS['r']}}}link")
            if rid:
                result.append(("image", rid))
        elif tag == f"{{{_DOCX_NS['v']}}}imagedata":
            rid = node.attrib.get(f"{{{_DOCX_NS['r']}}}id")
            if rid:
                result.append(("image", rid))
        elif tag in (f"{{{_DOCX_NS['w']}}}p", f"{{{_DOCX_NS['w']}}}tr"):
            result.append(("text", "\n"))
    return result
