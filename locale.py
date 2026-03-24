"""Сборщик переводов: locale/<code>/*.json -> assets/locale/<code>.json."""

from __future__ import annotations

import json
import sys
import sysconfig
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_stdlib_locale_module():
    stdlib_locale_path = Path(sysconfig.get_path("stdlib")) / "locale.py"
    spec = spec_from_file_location("_stdlib_locale", stdlib_locale_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load stdlib locale module from: {stdlib_locale_path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Compatibility shim: this file is named "locale.py" and may shadow stdlib "locale".
_stdlib_locale = _load_stdlib_locale_module()
normalize = _stdlib_locale.normalize


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _collect_language_dirs(locale_root: Path) -> list[Path]:
    if not locale_root.is_dir():
        return []
    return sorted(path for path in locale_root.iterdir() if path.is_dir())


def _collect_json_files(language_dir: Path) -> list[Path]:
    return sorted(path for path in language_dir.rglob("*.json") if path.is_file())


def _load_catalog(files: list[Path], language_code: str) -> dict[str, str]:
    catalog: dict[str, str] = {}
    for file_path in files:
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Locale file must contain JSON object: {file_path}")
        for key, value in raw.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"Locale keys and values must be strings: {file_path}")
            if key in catalog:
                raise ValueError(f"Duplicate locale key '{key}' in language '{language_code}': {file_path}")
            catalog[key] = value
    return catalog


def build_locales(locale_root: Path, output_root: Path) -> int:
    output_root.mkdir(parents=True, exist_ok=True)
    built = 0
    for language_dir in _collect_language_dirs(locale_root):
        code = language_dir.name.strip().lower().replace("-", "_")
        if not code:
            continue
        files = _collect_json_files(language_dir)
        if not files:
            continue
        catalog = _load_catalog(files, code)
        target_path = output_root / f"{code}.json"
        payload = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
        target_path.write_text(payload, encoding="utf-8")
        built += 1
        print(f"[locale] built: {target_path}")
    return built


def main() -> int:
    project_root = _project_root()
    locale_root = project_root / "locale"
    output_root = project_root / "assets" / "locale"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--locale-root" and i + 1 < len(args):
            locale_root = project_root / args[i + 1]
            i += 2
            continue
        if arg == "--output-root" and i + 1 < len(args):
            output_root = project_root / args[i + 1]
            i += 2
            continue
        raise ValueError(f"Unknown argument: {arg}")

    built = build_locales(locale_root, output_root)
    if built == 0:
        raise FileNotFoundError(f"No locale folders with JSON files found in: {locale_root}")
    print(f"[locale] done, languages built: {built}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

