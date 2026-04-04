"""Image helpers for extract cache: mainly encoding inputs as JPEG (PNG only where wired)."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path


CONVERT_TO_JPG = "jpg"
CONVERT_TO_PNG = "png"
CONVERT_TO_OPTIONS: tuple[str, ...] = (CONVERT_TO_JPG, CONVERT_TO_PNG)
JPEG_QUALITY: int = 90

_FORMAT_MAP = {
    CONVERT_TO_JPG: "JPEG",
    CONVERT_TO_PNG: "PNG",
}


def _target_format(convert_to: str) -> str:
    return _FORMAT_MAP.get(convert_to.lower(), "JPEG")


def _save_kwargs_for_format(pil_format: str) -> dict:
    if pil_format == "JPEG":
        return {"quality": JPEG_QUALITY}
    return {}


def _cap_long_edge_if_above(img, max_long_edge: int) -> None:
    """Shrink in place so max(width, height) ≤ max_long_edge; no change if already smaller."""
    if max_long_edge <= 0:
        return
    w, h = img.size
    if max(w, h) <= max_long_edge:
        return
    img.thumbnail((max_long_edge, max_long_edge))


def write_jpg_from_file(
    source_path: Path,
    dest_path: Path,
    *,
    source_ext: str | None = None,
    max_long_edge: int | None = None,
) -> None:
    """
    Decode a raster file or rasterize SVG, write JPEG.
    If max_long_edge > 0: cap long edge for both raster and SVG (downscale only; provider setting).
    """
    from PIL import Image

    save_kwargs = _save_kwargs_for_format("JPEG")
    ext = (source_ext or "").strip().lower()

    if ext == ".svg":
        from importlib import import_module
        cairosvg = import_module("cairosvg")
        png_bytes = cairosvg.svg2png(url=str(source_path))
        img = Image.open(BytesIO(png_bytes))
    else:
        img = Image.open(source_path)

    with img:
        if max_long_edge is not None and max_long_edge > 0:
            _cap_long_edge_if_above(img, max_long_edge)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(dest_path, format="JPEG", **save_kwargs)


def normalize_bytes(
    data: bytes,
    convert_to: str,
    max_size: int,
    source_ext: str,
) -> tuple[bytes, str]:
    """
    Convert image bytes to JPG or PNG (extract pipeline uses JPG).
    If max_size > 0: cap long edge after decode/rasterize for raster and SVG (downscale only; provider setting).
    Returns (result bytes, file extension with dot, e.g. ".jpg").
    On PIL error returns original data and original extension.
    """
    try:
        from PIL import Image
        target_format = _target_format(convert_to)
        target_ext = ".jpg" if target_format == "JPEG" else ".png"
        save_kwargs = _save_kwargs_for_format(target_format)
        ext = (source_ext or "").strip().lower()

        if ext == ".svg":
            from importlib import import_module
            cairosvg = import_module("cairosvg")
            png_bytes = cairosvg.svg2png(bytestring=data)
            img = Image.open(BytesIO(png_bytes))
            with img:
                if max_size > 0:
                    _cap_long_edge_if_above(img, max_size)
                if target_format == "JPEG" and img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                out = BytesIO()
                img.save(out, format=target_format, **save_kwargs)
                return out.getvalue(), target_ext

        with Image.open(BytesIO(data)) as img:
            if max_size > 0:
                _cap_long_edge_if_above(img, max_size)
            if target_format == "JPEG" and img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            out = BytesIO()
            img.save(out, format=target_format, **save_kwargs)
            return out.getvalue(), target_ext
    except Exception:
        ext = (source_ext or ".bin").strip()
        if not ext.startswith("."):
            ext = "." + ext
        return data, ext


def write_rgb_to_path(
    rgb_samples: bytes,
    width: int,
    height: int,
    dest_path: Path,
    convert_to: str,
) -> None:
    """
    Write raw RGB samples (e.g. fitz pixmap) to a JPG or PNG file.
    """
    from PIL import Image

    target_format = _target_format(convert_to)
    save_kwargs = _save_kwargs_for_format(target_format)
    img = Image.frombytes("RGB", (width, height), rgb_samples)
    img.save(dest_path, format=target_format, **save_kwargs)
