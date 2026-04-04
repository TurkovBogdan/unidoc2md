# Модуль file_extract
Модуль отвечает за извлечение контента из файлов и приведение результата к единому контракту для следующих стадий пайплайна

## Структура модуля
```text
src/modules/file_extract/
├─ __init__.py
├─ README.md
├─ bootstrap.py
├─ module.py
├─ interfaces/
│  └─ file_extract_provider.py
├─ models/
│  ├─ extract_config.py
│  ├─ extracted_document.py
│  └─ source_document.py
├─ providers/
│  ├─ file_extract_provider.py
│  ├─ providers_registry.py
│  └─ types/
│     ├─ text_extract_provider.py
│     ├─ markdown_extract_provider.py
│     ├─ image_extract_provider.py
│     ├─ pdf_extract/
│     └─ office_extract/
├─ schemas/
│  ├─ provider_config_builder.py
│  └─ provider_schema_builder.py
└─ services/
   ├─ file_extract_service.py
   └─ file_extract_cache.py
```

## Верхнеуровневая концепция
- вход модуля — `SourceDocument` и runtime-конфиг `ExtractConfig`
- `FileExtractService` выбирает провайдер по расширению файла
- ключ кеша считается как `compute_extract_hash(config, file_hash)`
- если результат уже есть в кеше, возвращается кешированная версия
- если кеша нет, вызывается `provider.extract(...)`, результат сохраняется и возвращается как `ExtractedDocument`

Ключевые точки:
- сервис: `src/modules/file_extract/services/file_extract_service.py`
- интерфейс провайдера: `src/modules/file_extract/interfaces/file_extract_provider.py`
- модели: `src/modules/file_extract/models/`

## Контракт результата провайдера
Любой провайдер должен вернуть объект `ExtractedDocument`

Структура `ExtractedDocument`:
- `source` — метаданные исходного документа в формате `DiscoveredDocument`
- `config` — использованный `ExtractConfig`
- `extract_hash` — hash ключ кеша для документа
- `content_hash` — опциональный hash агрегированного контента
- `content` — список элементов `ExtractedDocumentContent`

Структура `ExtractedDocumentContent`:
- `content_type` — тип носителя: `text`, `image`, `markdown`
- `semantic_type` — смысловая роль фрагмента:
  - `document_fragment`
  - `required_detection`
  - `markdown`
- `path` — путь к артефакту в кеше или `None`
- `mime_type` — MIME тип, если известен
- `content_hash` — hash содержимого, если рассчитан
- `value` — payload, если нужен на текущем этапе

Практическое правило:
- провайдер не должен возвращать сырой произвольный формат
- провайдер возвращает только `ExtractedDocument` с корректно заполненным `content`

## Интерфейс провайдера
Базовый интерфейс находится в `src/modules/file_extract/interfaces/file_extract_provider.py`

Что задаёт `FileExtractProvider`:
- `PROVIDER_CODE` — уникальный код провайдера в snake_case
- `provider_code()` — возвращает код провайдера
- `provider_title()` — код для локализации заголовка группы в UI
- `provider_description()` — описание группы настроек для UI
- `get_setting(config, key, default)` — чтение значения настройки провайдера из `ExtractConfig`

Обязательные методы, которые должен реализовать провайдер:
- `supported_extensions() -> set[str]`
- `project_settings_schema() -> tuple[SettingFieldSchema, ...]`
- `extract(source, config, storage, document_hash) -> ExtractedDocument`

Правила для обязательных методов:
- `supported_extensions()` возвращает расширения в lower-case и с ведущей точкой
- `project_settings_schema()` возвращает schema-поля, которые потом локализуются в GUI
- `extract(...)` возвращает только `ExtractedDocument` и сохраняет артефакты через `storage`

## Что именно должен возвращать провайдер
Минимально валидный результат:
- `ExtractedDocument.source` с данными текущего файла
- `ExtractedDocument.extract_hash` равный `document_hash`, который пришёл в `extract(...)`
- `ExtractedDocument.content` — список элементов `ExtractedDocumentContent`

Если извлекать нечего:
- возвращается `ExtractedDocument(..., content=[])`
- это корректный сценарий, например режим `skip`

## Добавление собственного провайдера
Ниже сценарий по образцу `src/modules/file_extract/providers/types/text_extract_provider.py`

### 1. Создать класс провайдера
Наследоваться от `FileExtractProvider` и задать `PROVIDER_CODE`

```python
class MyFormatExtractProvider(FileExtractProvider):
    PROVIDER_CODE = "my_format_extract_provider"
```

### 2. Описать поддерживаемые расширения
Реализовать `supported_extensions()` и вернуть `set[str]`

```python
@staticmethod
def supported_extensions() -> set[str]:
    return {".myext"}
```

### 3. Добавить схему настроек провайдера
Реализовать `project_settings_schema()` через `SettingFieldSchema`

```python
@classmethod
def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
    return (
        SettingFieldSchema(
            key="algorithm",
            type="select",
            default="default_mode",
            label="algorithm",
            description="",
            options=(("default_mode", "default_mode"), ("skip", "skip")),
        ),
    )
```

### 4. Реализовать extract
Сигнатура обязательна:

```python
def extract(
    self,
    source: SourceDocument,
    config: ExtractConfig,
    storage: FileExtractCacheService,
    document_hash: str,
) -> ExtractedDocument:
    ...
```

Рекомендуемый шаблон:
- прочитать настройки провайдера через `self.get_setting(config, "...")`
- обработать `skip` режим и вернуть `content=[]`
- извлечь контент из `source.path_obj()`
- сохранить артефакт через `storage.save_text_content(...)` или аналог
- собрать `ExtractedDocumentContent`
- вернуть `ExtractedDocument`

### 5. Заполнить semantic_type осмысленно
- обычный текстовый фрагмент: `SEMANTIC_TYPE_DOCUMENT_FRAGMENT`
- markdown как финальный markdown-фрагмент: `SEMANTIC_TYPE_MARKDOWN`
- контент, который требует последующего распознавания: `SEMANTIC_TYPE_REQUIRED_DETECTION`

### 6. Проверить контракт
Перед подключением провайдера проверь:
- `content_type` и `semantic_type` валидны
- `path` указывает на кеш-артефакт или `None` осознанно
- при пустом результате возвращается `ExtractedDocument`, а не `None`

## Пример поведения text-провайдера
`TextExtractProvider` делает базовый референсный сценарий:
- поддерживает `.txt`
- имеет настройку `algorithm` с режимами `only_text` и `skip`
- в режиме `skip` возвращает пустой `content`
- читает текст файла в UTF-8
- сохраняет фрагмент через `storage.save_text_content(...)`
- возвращает `ExtractedDocument` со списком контента

Этот провайдер можно использовать как эталон структуры для новых форматов
