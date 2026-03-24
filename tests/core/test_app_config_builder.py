"""Тесты AppConfigBuilder: создание app.ini, merge недостающих ключей, идемпотентность, парсинг."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core import AppConfig, AppConfigStore
from src.core.models.core_config import CoreConfig
from src.modules.llm_providers.module import LLMProvidersConfig
from src.modules.yandex_ocr.module import YandexOCRConfig


def _minimal_ini_llm_providers() -> str:
    return (
        "ANTHROPIC_PROVIDER_ENABLED = false\nANTHROPIC_API_KEY =\n"
        "GOOGLE_PROVIDER_ENABLED = false\nGOOGLE_API_KEY =\n"
        "OPENAI_PROVIDER_ENABLED = false\nOPENAI_API_KEY =\n"
        "XAI_PROVIDER_ENABLED = false\nXAI_API_KEY =\n"
    )


def _minimal_ini_yandex_ocr() -> str:
    return "PROVIDER_ENABLED = false\nKEY_ID =\nKEY_SECRET =\n"


def test_load_or_create_creates_ini_when_missing(tmp_path: Path) -> None:
    assert not (tmp_path / "app.ini").exists()
    config = AppConfigStore.load_or_create(tmp_path)
    ini_path = tmp_path / "app.ini"
    assert ini_path.exists()
    content = ini_path.read_text(encoding="utf-8")
    assert "[CORE]" in content
    assert "LEVEL" in content
    assert "[LLM_PROVIDERS]" in content
    assert "[YANDEX_OCR]" in content
    assert "ANTHROPIC_PROVIDER_ENABLED" in content
    assert "ANTHROPIC_API_KEY" in content
    assert "OPENAI_API_KEY" in content
    assert config.core.debug is False
    assert config.core.log_level == "DEBUG"
    assert config.llm_providers.anthropic_api_key == ""
    assert config.llm_providers.anthropic_provider_enabled is False
    assert config.llm_providers.openai_provider_enabled is False
    assert config.yandex_ocr.key_secret == ""


def test_load_or_create_merge_adds_missing_section_and_keys(tmp_path: Path) -> None:
    (tmp_path / "app.ini").write_text(
        "[CORE]\nDEBUG = true\nLEVEL = DEBUG\nCONSOLE_LEVEL = INFO\n\n"
        "[LLM_PROVIDERS]\nANTHROPIC_API_KEY = sk-xxx\n\n[YANDEX_OCR]\n",
        encoding="utf-8",
    )
    config = AppConfigStore.load_or_create(tmp_path)
    content = (tmp_path / "app.ini").read_text(encoding="utf-8")
    assert "ANTHROPIC_PROVIDER_ENABLED" in content
    assert "ANTHROPIC_API_KEY" in content
    assert config.llm_providers.anthropic_api_key == "sk-xxx"
    assert config.llm_providers.anthropic_provider_enabled is False
    assert config.core.debug is True
    assert config.core.log_level == "DEBUG"


def test_load_or_create_idempotent_when_ini_complete(tmp_path: Path) -> None:
    AppConfigStore.load_or_create(tmp_path)
    first_content = (tmp_path / "app.ini").read_text(encoding="utf-8")
    AppConfigStore.load_or_create(tmp_path)
    second_content = (tmp_path / "app.ini").read_text(encoding="utf-8")
    assert first_content == second_content


def test_parser_core_debug_bool(tmp_path: Path) -> None:
    (tmp_path / "app.ini").write_text(
        "[CORE]\nDEBUG = true\nLEVEL = DEBUG\nCONSOLE_LEVEL = INFO\n\n"
        "[LLM_PROVIDERS]\n" + _minimal_ini_llm_providers() + "\n[YANDEX_OCR]\n" + _minimal_ini_yandex_ocr(),
        encoding="utf-8",
    )
    config = AppConfigStore.load_or_create(tmp_path)
    assert config.core.debug is True

    (tmp_path / "app.ini").write_text(
        "[CORE]\nDEBUG = false\nLEVEL = DEBUG\nCONSOLE_LEVEL = INFO\n\n"
        "[LLM_PROVIDERS]\n" + _minimal_ini_llm_providers() + "\n[YANDEX_OCR]\n" + _minimal_ini_yandex_ocr(),
        encoding="utf-8",
    )
    config2 = AppConfigStore.load_or_create(tmp_path)
    assert config2.core.debug is False


def test_llm_providers_keys_preserved(tmp_path: Path) -> None:
    (tmp_path / "app.ini").write_text(
        "[CORE]\nDEBUG = false\nLEVEL = DEBUG\nCONSOLE_LEVEL = INFO\n\n"
        "[LLM_PROVIDERS]\n"
        "ANTHROPIC_PROVIDER_ENABLED = false\nANTHROPIC_API_KEY = key1\n"
        "GOOGLE_PROVIDER_ENABLED = false\nGOOGLE_API_KEY =\n"
        "OPENAI_PROVIDER_ENABLED = false\nOPENAI_API_KEY =\n"
        "XAI_PROVIDER_ENABLED = false\nXAI_API_KEY =\n\n"
        "[YANDEX_OCR]\nPROVIDER_ENABLED = false\nKEY_ID =\nKEY_SECRET = secret\n",
        encoding="utf-8",
    )
    config = AppConfigStore.load_or_create(tmp_path)
    assert config.llm_providers.anthropic_api_key == "key1"
    assert config.llm_providers.openai_api_key == ""
    assert config.yandex_ocr.key_secret == "secret"


def test_app_config_store_returns_default_before_load() -> None:
    AppConfigStore.reset()
    config = AppConfigStore.get()
    assert isinstance(config, AppConfig)
    assert config.core == CoreConfig()
    assert config.llm_providers.anthropic_api_key == ""
    assert config.core.log_level == "DEBUG"


def test_app_config_store_returns_current_after_load(tmp_path: Path) -> None:
    (tmp_path / "app.ini").write_text(
        "[CORE]\nDEBUG = true\nLEVEL = DEBUG\nCONSOLE_LEVEL = INFO\n\n"
        "[LLM_PROVIDERS]\n" + _minimal_ini_llm_providers().replace("ANTHROPIC_API_KEY =\n", "ANTHROPIC_API_KEY = x\n")
        + "\n[YANDEX_OCR]\n" + _minimal_ini_yandex_ocr(),
        encoding="utf-8",
    )
    AppConfigStore.load_or_create(tmp_path)
    config = AppConfigStore.get()
    assert config.core.debug is True
    assert config.llm_providers.anthropic_api_key == "x"


def test_store_reset_returns_default_from_get() -> None:
    AppConfigStore.set(
        AppConfig(core=CoreConfig(debug=True), llm_providers=LLMProvidersConfig(), yandex_ocr=YandexOCRConfig())
    )
    assert AppConfigStore.get().core.debug is True
    AppConfigStore.reset()
    config = AppConfigStore.get()
    assert config == AppConfig.default()
    assert config.core.debug is False


def _token_status_from_store() -> dict[str, bool]:
    lp = AppConfigStore.get().llm_providers
    return {
        "openai": bool((lp.openai_api_key or "").strip()),
        "anthropic": bool((lp.anthropic_api_key or "").strip()),
    }


def test_token_status_uses_app_ini_llm_providers() -> None:
    AppConfigStore.set(
        AppConfig(
            core=CoreConfig(),
            llm_providers=LLMProvidersConfig(openai_api_key="sk-test", anthropic_api_key=""),
            yandex_ocr=YandexOCRConfig(),
        )
    )
    try:
        status = _token_status_from_store()
        assert status.get("openai") is True
        assert status.get("anthropic") is False
    finally:
        AppConfigStore.reset()


def test_get_token_status_reads_config_at_call_time() -> None:
    AppConfigStore.set(
        AppConfig(
            core=CoreConfig(),
            llm_providers=LLMProvidersConfig(openai_api_key="sk-first", anthropic_api_key=""),
            yandex_ocr=YandexOCRConfig(),
        )
    )
    try:
        status1 = _token_status_from_store()
        assert status1.get("openai") is True

        AppConfigStore.set(
            AppConfig(
                core=CoreConfig(),
                llm_providers=LLMProvidersConfig(openai_api_key="", anthropic_api_key="key-second"),
                yandex_ocr=YandexOCRConfig(),
            )
        )
        status2 = _token_status_from_store()
        assert status2.get("openai") is False
        assert status2.get("anthropic") is True
    finally:
        AppConfigStore.reset()
