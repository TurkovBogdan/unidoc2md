"""Секция tagging: режим (пропуск / LLM), флаги вывода, провайдер, модель, доп. текст, стартовый набор тегов."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

# Допустимые значения tag_format (коды в UI и в конфиге)
TAGGING_TAG_FORMAT_VALID: frozenset[str] = frozenset({"Tag_name", "tag_name"})

# Режим этапа: второй элемент — msgid для locmsg (locale/*/project_tagging.json)
TAGGING_MODES = SimpleNamespace(
    skip="skip",
    create_document_tags_linear="create_document_tags_linear",
    create_document_tags_parallel="create_document_tags_parallel",
    options=(
        ("skip", "project_tagging.logic.skip"),
        ("create_document_tags_linear", "project_tagging.logic.linear"),
        ("create_document_tags_parallel", "project_tagging.logic.parallel"),
    ),
    valid_codes=frozenset(
        {
            "skip",
            "create_document_tags_linear",
            "create_document_tags_parallel",
        }
    ),
)

# GUI: заголовок первого ряда (Header3 + комбо), как pipeline create_documents_index_heading.
TAGGING_GUI_MODE_HEADING_MSGID = "project_tagging.mode_field_label"

TAGGING_LLM_MODES = frozenset(
    {
        TAGGING_MODES.create_document_tags_linear,
        TAGGING_MODES.create_document_tags_parallel,
    }
)

# Значения поля logic в payload/progress_sink (GUI и сводка этапа)
TAGGING_PAYLOAD_LOGIC = SimpleNamespace(
    skip="tagging_skip",
    no_llm="tagging_no_llm",
    create_tags_field_off="tagging_create_tags_field_off",
    llm="tagging_llm",
)

TAGGING_DEFAULTS = SimpleNamespace(
    tagging_mode=TAGGING_MODES.create_document_tags_parallel,
    tag_format="Tag_name",
    create_tags_field=True,
    create_description_field=True,
    create_date_field=False,
    llm_provider="",
    llm_model="",
    llm_reasoning="low",
    llm_temperature=0.3,
    llm_additional_instructions="",
    start_tag_set="",
)

TAGGING_KEYS = SimpleNamespace(
    tagging_mode="tagging_mode",
    tag_format="tag_format",
    create_tags_field="create_tags_field",
    create_description_field="create_description_field",
    create_date_field="create_date_field",
    llm_provider="llm_provider",
    llm_model="llm_model",
    llm_reasoning="llm_reasoning",
    llm_temperature="llm_temperature",
    llm_additional_instructions="llm_additional_instructions",
    start_tag_set="start_tag_set",
)


TAGGING_UI_FIRST_SECTION = SimpleNamespace(
    title_msgid="project_tagging.section_primary_title",
    description_msgid="project_tagging.section_primary_description",
)

class TaggingConfig:
    """Умолчания и валидация секции tagging."""

    TAGGING_TAG_FORMAT_VALID = TAGGING_TAG_FORMAT_VALID
    TAGGING_MODES = TAGGING_MODES
    TAGGING_LLM_MODES = TAGGING_LLM_MODES
    TAGGING_PAYLOAD_LOGIC = TAGGING_PAYLOAD_LOGIC
    TAGGING_DEFAULTS = TAGGING_DEFAULTS
    TAGGING_KEYS = TAGGING_KEYS
    UI_FIRST_SECTION = TAGGING_UI_FIRST_SECTION

    @staticmethod
    def get_default() -> dict[str, Any]:
        """Возвращает словарь умолчаний для секции tagging."""
        D = TAGGING_DEFAULTS
        K = TAGGING_KEYS
        return {
            K.tagging_mode: D.tagging_mode,
            K.tag_format: D.tag_format,
            K.create_tags_field: D.create_tags_field,
            K.create_description_field: D.create_description_field,
            K.create_date_field: D.create_date_field,
            K.llm_provider: D.llm_provider,
            K.llm_model: D.llm_model,
            K.llm_reasoning: D.llm_reasoning,
            K.llm_temperature: D.llm_temperature,
            K.llm_additional_instructions: D.llm_additional_instructions,
            K.start_tag_set: D.start_tag_set,
        }

    @staticmethod
    def coerce_bool(value: Any, default: bool) -> bool:
        """Приведение к bool при чтении конфига (JSON, редкие строковые значения)."""
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            if value == 1:
                return True
            if value == 0:
                return False
        if isinstance(value, str):
            v = value.strip().lower()
            if v in ("true", "1", "yes", "да"):
                return True
            if v in ("false", "0", "no", "нет"):
                return False
        return default

    @staticmethod
    def coerce_tag_format(value: Any, default: str) -> str:
        if value is None:
            return default
        s = str(value).strip()
        if s in TAGGING_TAG_FORMAT_VALID:
            return s
        return default

    @staticmethod
    def with_normalized_bools(tagging: dict[str, Any]) -> dict[str, Any]:
        """Копия секции с каноническими bool по ключам create_tags_field / create_description_field / create_date_field."""
        K = TAGGING_KEYS
        D = TAGGING_DEFAULTS
        t = dict(tagging)
        t[K.create_tags_field] = TaggingConfig.coerce_bool(
            t.get(K.create_tags_field), D.create_tags_field
        )
        t[K.create_description_field] = TaggingConfig.coerce_bool(
            t.get(K.create_description_field), D.create_description_field
        )
        t[K.create_date_field] = TaggingConfig.coerce_bool(
            t.get(K.create_date_field), D.create_date_field
        )
        t[K.tag_format] = TaggingConfig.coerce_tag_format(
            t.get(K.tag_format), D.tag_format
        )
        return t

    @staticmethod
    def validate(data: Any) -> list[str]:
        """Проверяет данные секции tagging. Возвращает список сообщений об ошибках."""
        errors: list[str] = []
        if not isinstance(data, dict):
            errors.append("Tagging: ожидается объект (dict).")
            return errors
        K = TAGGING_KEYS
        M = TAGGING_MODES
        D = TAGGING_DEFAULTS
        mode = data.get(K.tagging_mode) or D.tagging_mode
        if isinstance(mode, str):
            mode = mode.strip().lower()
        else:
            mode = ""
        if mode == "create_document_tags":
            mode = M.create_document_tags_linear
        if mode not in M.valid_codes:
            errors.append(
                f"Tagging: tagging_mode должен быть один из: {', '.join(sorted(M.valid_codes))}."
            )
        tf = data.get(K.tag_format)
        if tf is not None:
            if not isinstance(tf, str) or str(tf).strip() not in TAGGING_TAG_FORMAT_VALID:
                errors.append(
                    f"Tagging: tag_format должен быть один из: {', '.join(sorted(TAGGING_TAG_FORMAT_VALID))}."
                )
        for bool_key in (K.create_tags_field, K.create_description_field, K.create_date_field):
            val = data.get(bool_key)
            if val is not None and not isinstance(val, bool):
                errors.append(f"Tagging: поле {bool_key} должно быть true/false (bool).")
        for key in (
            K.llm_provider,
            K.llm_model,
            K.llm_reasoning,
            K.llm_additional_instructions,
            K.start_tag_set,
        ):
            val = data.get(key)
            if val is not None and not isinstance(val, str):
                errors.append(f"Tagging: поле {key} должно быть строкой.")
        t = data.get(K.llm_temperature)
        if t is not None:
            try:
                tf = float(t)
                if not (0.0 <= tf <= 2.0):
                    errors.append("Tagging: llm_temperature должен быть от 0.0 до 2.0.")
            except (TypeError, ValueError):
                errors.append("Tagging: llm_temperature должен быть числом.")
        reason = (data.get(K.llm_reasoning) or "").strip().lower()
        if reason and reason not in ("disabled", "low", "medium", "high"):
            errors.append(
                "Tagging: llm_reasoning должен быть один из: disabled, low, medium, high."
            )
        return errors
