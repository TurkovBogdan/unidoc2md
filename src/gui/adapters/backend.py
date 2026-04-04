"""Backend calls from the GUI layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core import AppConfig
from src.core.models.core_config import CoreConfig
from src.modules.llm_providers.module import LLMProvidersConfig, llm_providers_set_providers_config
from src.modules.yandex_ocr.module import YandexOCRConfig, yandex_ocr_set_api_config
from src.modules.file_discovery import DiscoveryService
from src.modules.file_discovery.models import DiscoveryConfig
from src.modules.file_extract import get_supported_extensions
from src.modules.project import (
    ProjectInfo,
    ProjectManager,
    load_project_config,
    load_project_config_dict,
    save_project_config_dict,
    validate_project_config,
)


def _get_token_status() -> dict[str, bool]:
    """Stub: token presence is not verified."""
    return {}


def _docs_count_for_project(project_root: Path) -> int:
    """Count files under project ``docs/`` using the same extensions and ``recursive_search`` as the project files tab."""
    docs_dir = project_root / "docs"
    if not docs_dir.is_dir():
        return 0
    try:
        config = load_project_config(project_root)
        extensions = get_supported_extensions()
        if not extensions:
            extensions = {"*"}
        discovery = DiscoveryService()
        discovery_config = DiscoveryConfig(
            path=str(docs_dir),
            extensions=extensions,
            hash=False,
            recursive_search=config.discovery.get("recursive_search", False),
        )
        return len(discovery.discover_files(discovery_config))
    except Exception:
        return 0


def load_projects(app_root: Path) -> list[ProjectInfo]:
    """Return projects with path and ``docs_count`` (files to process)."""
    projects = ProjectManager(app_root).list_projects()
    return [
        ProjectInfo(id=p.id, path=p.path, docs_count=_docs_count_for_project(p.path))
        for p in projects
    ]


def remove_project(app_root: Path, project_root: Path) -> None:
    """Remove a project by its root path."""
    ProjectManager(app_root).delete(project_root)


def create_project(app_root: Path, name: str) -> Path:
    """Create a project with default settings; returns ``project_root``."""
    return ProjectManager(app_root).create(name)


def validate_config(project_root: Path, config_data: dict | None = None) -> tuple[bool, list[str], list[str]]:
    """Validate config; returns ``(is_valid, errors, warnings)``."""
    result = validate_project_config(project_root, config_data=config_data, check_tokens=True)
    return result.is_valid, result.errors, result.warnings


def get_api_token_status() -> dict[str, bool]:
    """Per-provider API token fill status (stub)."""
    return _get_token_status()


def load_app_config_dict() -> dict[str, Any]:
    """Load ``app.ini`` into a dict for the settings screen. Requires prior ``AppConfigStore.load_or_create()``."""
    from src.core import AppConfigStore

    cfg = AppConfigStore.get()
    lp = cfg.llm_providers
    yo = cfg.yandex_ocr
    return {
        "core": {
            "debug": cfg.core.debug,
            "log_level": cfg.core.log_level or "DEBUG",
            "console_log_level": cfg.core.console_log_level or "INFO",
            "language": (cfg.core.language or "").strip(),
        },
        "llm_providers": {
            "gateway_connect_timeout": getattr(lp, "gateway_connect_timeout", 30),
            "gateway_read_timeout": getattr(lp, "gateway_read_timeout", 600),
            "anthropic_provider_enabled": lp.anthropic_provider_enabled,
            "anthropic_api_key": lp.anthropic_api_key or "",
            "google_provider_enabled": lp.google_provider_enabled,
            "google_api_key": lp.google_api_key or "",
            "openai_provider_enabled": lp.openai_provider_enabled,
            "openai_api_key": lp.openai_api_key or "",
            "xai_provider_enabled": lp.xai_provider_enabled,
            "xai_api_key": lp.xai_api_key or "",
            "lmstudio_provider_enabled": lp.lmstudio_provider_enabled,
            "lmstudio_host": lp.lmstudio_host or "",
            "lmstudio_port": lp.lmstudio_port or "",
            "lmstudio_ssl": lp.lmstudio_ssl,
            "lmstudio_api_key": lp.lmstudio_api_key or "",
        },
        "yandex_ocr": {
            "provider_enabled": yo.provider_enabled,
            "key_id": yo.key_id or "",
            "key_secret": yo.key_secret or "",
        },
    }


def _llm_int_clamped(lp: dict[str, Any], key: str, default: int, lo: int, hi: int) -> int:
    try:
        val = int(lp.get(key, default))
    except (TypeError, ValueError):
        val = default
    return max(lo, min(hi, val))


def save_app_config_dict(data: dict[str, Any], *, app_root: Path | None = None) -> None:
    """Persist settings dict to ``app.ini`` and refresh runtime config in AppConfigStore, llm_providers, and yandex_ocr.
    UI language is applied via ``set_language`` after write.
    ``app_root`` must match ``load_or_create``; ``None`` uses ``resolve_runtime_root``."""
    from src.core import AppConfigStore
    from src.core.app_locale import AVAILABLE_LANGUAGES, set_language

    core = data.get("core") or {}
    lp = data.get("llm_providers") or {}
    yo = data.get("yandex_ocr") or {}
    lang_raw = str(core.get("language", "")).strip()
    lang_norm = lang_raw.lower().replace("-", "_")
    lang_stored = lang_norm if lang_norm in AVAILABLE_LANGUAGES else lang_raw
    config = AppConfig(
        core=CoreConfig(
            debug=bool(core.get("debug", False)),
            log_level=str(core.get("log_level", "DEBUG")).strip() or "DEBUG",
            console_log_level=str(core.get("console_log_level", "INFO")).strip() or "INFO",
            language=lang_stored,
        ),
        llm_providers=LLMProvidersConfig(
            gateway_connect_timeout=_llm_int_clamped(lp, "gateway_connect_timeout", 30, 1, 120),
            gateway_read_timeout=_llm_int_clamped(lp, "gateway_read_timeout", 600, 60, 7200),
            anthropic_provider_enabled=bool(lp.get("anthropic_provider_enabled", False)),
            anthropic_api_key=str(lp.get("anthropic_api_key", "")),
            google_provider_enabled=bool(lp.get("google_provider_enabled", False)),
            google_api_key=str(lp.get("google_api_key", "")),
            openai_provider_enabled=bool(lp.get("openai_provider_enabled", False)),
            openai_api_key=str(lp.get("openai_api_key", "")),
            xai_provider_enabled=bool(lp.get("xai_provider_enabled", False)),
            xai_api_key=str(lp.get("xai_api_key", "")),
            lmstudio_provider_enabled=bool(lp.get("lmstudio_provider_enabled", False)),
            lmstudio_host=str(lp.get("lmstudio_host", "")).strip(),
            lmstudio_port=str(lp.get("lmstudio_port", "")).strip(),
            lmstudio_ssl=bool(lp.get("lmstudio_ssl", False)),
            lmstudio_api_key=str(lp.get("lmstudio_api_key", "")),
        ),
        yandex_ocr=YandexOCRConfig(
            provider_enabled=bool(yo.get("provider_enabled", False)),
            key_id=str(yo.get("key_id", "")),
            key_secret=str(yo.get("key_secret", "")),
        ),
    )
    AppConfigStore.save(config, app_root)
    if lang_norm in AVAILABLE_LANGUAGES:
        set_language(lang_norm)
    llm_providers_set_providers_config(config.llm_providers)
    yandex_ocr_set_api_config(config.yandex_ocr)
