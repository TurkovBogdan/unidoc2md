"""Тесты prepare_core_runtime: только app-level инфраструктура, без доменных файлов."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core import AppConfigStore
from src.core.bootstrap import CoreBootstrap, prepare_core_runtime
from src.core.app_path import AppPath
from src.core.logger import set_system_logger

_TEST_LANGUAGES = {
    "ru": "Русский",
    "en": "English",
    "zh": "中文",
}


@pytest.fixture(autouse=True)
def _reset_core_state_after_bootstrap_tests() -> None:
    """Сбрасываем store и логгер после каждого теста, чтобы не влиять на другие тесты."""
    yield
    AppConfigStore.reset()
    set_system_logger(None)


def test_prepare_core_runtime_returns_app_path(tmp_path: Path) -> None:
    paths = prepare_core_runtime(tmp_path)
    assert isinstance(paths, AppPath)
    assert paths.root == tmp_path


def test_prepare_core_runtime_creates_app_dirs(tmp_path: Path) -> None:
    prepare_core_runtime(tmp_path)
    assert (tmp_path / "projects").is_dir()
    assert (tmp_path / "data").is_dir()
    assert (tmp_path / "data" / "source").is_dir()
    assert (tmp_path / "data" / "user").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "cache").is_dir()
    assert (tmp_path / "temp").is_dir()
    assert (tmp_path / "assets" / "locale").is_dir()


def test_prepare_core_runtime_copies_locale_assets(tmp_path: Path) -> None:
    paths = prepare_core_runtime(tmp_path)
    CoreBootstrap.lang_boot(paths, _TEST_LANGUAGES)
    locale_dir = tmp_path / "assets" / "locale"
    assert (locale_dir / "ru.json").is_file()
    assert (locale_dir / "en.json").is_file()
    assert (locale_dir / "zh.json").is_file()


def test_prepare_core_runtime_creates_app_ini(tmp_path: Path) -> None:
    prepare_core_runtime(tmp_path)
    assert (tmp_path / "app.ini").exists()
    content = (tmp_path / "app.ini").read_text(encoding="utf-8")
    assert "[CORE]" in content
    assert "[LLM_PROVIDERS]" in content
    assert "[YANDEX_OCR]" in content


def test_prepare_core_runtime_does_not_create_domain_files(tmp_path: Path) -> None:
    """core не создаёт доменные файлы llm_providers и llm_model_registry."""
    prepare_core_runtime(tmp_path)
    assert not (tmp_path / "data" / "openai-image-support.txt").exists()
    assert not (tmp_path / "data" / "yandex-image-support.txt").exists()
    assert not (tmp_path / "data" / "user" / "gateway_models.json").exists()


def test_prepare_core_runtime_idempotent(tmp_path: Path) -> None:
    p1 = prepare_core_runtime(tmp_path)
    p2 = prepare_core_runtime(tmp_path)
    assert p1.root == p2.root
    assert (tmp_path / "app.ini").exists()


def test_lang_boot_requires_languages(tmp_path: Path) -> None:
    paths = prepare_core_runtime(tmp_path)
    with pytest.raises(ValueError):
        CoreBootstrap.lang_boot(paths)
