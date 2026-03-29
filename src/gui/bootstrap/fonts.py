"""
Cross-platform registration of custom fonts for Tkinter.

Used during GUI bootstrap. Registers a font from a ``.ttf`` / ``.otf`` file:
on Windows, load into the session; on Linux/macOS, copy into the user fonts directory.
"""

from __future__ import annotations

import shutil
import struct
import subprocess
import sys
from pathlib import Path

from src.core.app_path import project_root

APP_FONT_REGULAR = "JetBrainsMono-Regular.ttf"


def _resolve_app_font_path(app_root: Path) -> Path | None:
    """
    Resolve the TTF path for registration.

    - Dev (e.g. ``tools/win-dev-run.bat``, ``APP_PROFILE=dev``): ``app_root`` is
      ``runtime/<profile>``; font lives in ``<project_root>/assets/fonts/`` (and optionally under runtime).
    - Frozen (PyInstaller): font in ``sys._MEIPASS/assets/fonts/`` or next to the exe in
      ``<app_root>/assets/fonts/``.
    """
    app_root = Path(app_root)
    name = APP_FONT_REGULAR
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        candidates.append(app_root / "assets" / "fonts" / name)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "assets" / "fonts" / name)
    else:
        candidates.append(app_root / "assets" / "fonts" / name)
        candidates.append(project_root() / "assets" / "fonts" / name)

    for p in candidates:
        if p.is_file():
            return p.resolve()
    return None


def get_font_family_from_file(path: Path) -> str | None:
    """
    Read the font family name from a TTF/OTF file (``name`` table, nameID 1).
    Returns ``None`` on error or if the name is missing.
    """
    path = Path(path)
    if not path.is_file():
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    if len(data) < 12:
        return None
    num_tables = struct.unpack_from(">H", data, 4)[0]
    if len(data) < 12 + num_tables * 16:
        return None
    name_offset = None
    name_length = None
    for i in range(num_tables):
        off = 12 + i * 16
        tag = data[off : off + 4].decode("ascii", errors="ignore")
        if tag == "name":
            name_offset = struct.unpack_from(">I", data, off + 8)[0]
            name_length = struct.unpack_from(">I", data, off + 12)[0]
            break
    if name_offset is None or name_length is None or name_offset + name_length > len(data):
        return None
    name_data = data[name_offset : name_offset + name_length]
    if len(name_data) < 6:
        return None
    format_ = struct.unpack_from(">H", name_data, 0)[0]
    count = struct.unpack_from(">H", name_data, 2)[0]
    string_offset = struct.unpack_from(">H", name_data, 4)[0]
    for i in range(count):
        rec_off = 6 + i * 12
        if rec_off + 12 > len(name_data):
            break
        platform_id, encoding_id, language_id, name_id, length, offset = struct.unpack_from(
            ">HHHHHH", name_data, rec_off
        )
        if name_id != 1:
            continue
        start = string_offset + offset
        if start < 0 or start + length > len(name_data):
            continue
        raw = name_data[start : start + length]
        if platform_id == 3:
            try:
                return raw.decode("utf-16-be").strip("\x00")
            except UnicodeDecodeError:
                continue
        if platform_id == 0:
            try:
                return raw.decode("utf-16-be").strip("\x00")
            except UnicodeDecodeError:
                continue
        if platform_id == 1 and raw:
            try:
                return raw.decode("mac-roman", errors="replace").strip("\x00")
            except Exception:
                continue
    return None


def register_font(path: Path, family_name: str | None = None) -> str | None:
    """
    Register a font file and return the family name for Tk.
    Windows: load into the session. Linux/macOS: copy into the user fonts directory.
    """
    path = Path(path).resolve()
    if not path.is_file():
        return None
    suffix = path.suffix.lower()
    if suffix not in (".ttf", ".otf"):
        return None

    name = family_name or get_font_family_from_file(path)
    if not name:
        return None

    if sys.platform == "win32":
        return _register_font_windows(path, name)
    if sys.platform == "darwin":
        return _register_font_macos(path, name)
    if sys.platform == "linux":
        return _register_font_linux(path, name)
    return name


def _register_font_windows(path: Path, family_name: str) -> str | None:
    try:
        import ctypes

        gdi32 = ctypes.windll.gdi32  # type: ignore[attr-defined]
        FR_PRIVATE = 0x10
        added = gdi32.AddFontResourceExW(str(path), FR_PRIVATE, 0)
        if added:
            return family_name
        return None
    except Exception:
        return None


def _register_font_linux(path: Path, family_name: str) -> str | None:
    fonts_dir = Path.home() / ".local" / "share" / "fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    dest = fonts_dir / path.name
    try:
        shutil.copy2(path, dest)
    except OSError:
        return None
    try:
        subprocess.run(
            ["fc-cache", "-f", "-v"],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return family_name


def _register_font_macos(path: Path, family_name: str) -> str | None:
    fonts_dir = Path.home() / "Library" / "Fonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)
    dest = fonts_dir / path.name
    try:
        shutil.copy2(path, dest)
    except OSError:
        return None
    return family_name


def ensure_app_fonts(app_root: Path) -> str | None:
    """
    Locate the app font and register it for Tk/GDI.

    Search order: ``_resolve_app_font_path``. For frozen builds, registration may use
    ``_MEIPASS`` directly (no copy next to the exe required).

    When frozen, also tries to copy the TTF into ``<app_root>/assets/fonts/`` if the
    source is the bundle (write failures are ignored).

    :return: Font family name, or ``None`` to use the theme fallback.
    """
    app_root = Path(app_root)
    font_path = _resolve_app_font_path(app_root)
    if font_path is None:
        return None

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundle_file = (Path(meipass) / "assets" / "fonts" / APP_FONT_REGULAR).resolve()
            if bundle_file.is_file():
                try:
                    if font_path.samefile(bundle_file):
                        dest_dir = app_root / "assets" / "fonts"
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(bundle_file, dest_dir / APP_FONT_REGULAR)
                except OSError:
                    pass

    return register_font(font_path)


class GuiFontPreparator:
    """Prepare app fonts for the UI (register and copy when needed)."""

    def prepare(self, app_root: Path) -> str | None:
        """
        Ensure the app font exists and is registered.

        :param app_root: Application root directory.
        :return: Font family name for the UI, or ``None`` for fallback.
        """
        return ensure_app_fonts(Path(app_root))
