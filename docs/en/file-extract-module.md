# The `file_extract` module
This module extracts content from files and normalizes it to a single contract for later pipeline stages

## Module layout
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

## High-level design
- Module input: `SourceDocument` and runtime config `ExtractConfig`
- `FileExtractService` picks a provider by file extension
- Cache key is `compute_extract_hash(config, file_hash)`
- If a result is already cached, the cached version is returned
- If not, `provider.extract(...)` runs; the result is stored and returned as `ExtractedDocument`

Important locations:
- service: `src/modules/file_extract/services/file_extract_service.py`
- provider interface: `src/modules/file_extract/interfaces/file_extract_provider.py`
- models: `src/modules/file_extract/models/`

## Provider result contract
Every provider must return an `ExtractedDocument` instance

`ExtractedDocument` fields:
- `source` — source document metadata as `DiscoveredDocument`
- `config` — `ExtractConfig` that was used
- `extract_hash` — cache key hash for the document
- `content_hash` — optional hash of aggregated content
- `content` — list of `ExtractedDocumentContent` items

`ExtractedDocumentContent` fields:
- `content_type` — carrier type: `text`, `image`, `markdown`
- `semantic_type` — semantic role of the fragment:
  - `document_fragment`
  - `required_detection`
  - `markdown`
- `path` — path to a cache artifact, or `None`
- `mime_type` — MIME type when known
- `content_hash` — content hash when computed
- `value` — payload when needed at this stage

Practical rules:
- providers must not return raw arbitrary formats
- providers return only `ExtractedDocument` with a correctly filled `content`

## Provider interface
The base interface lives in `src/modules/file_extract/interfaces/file_extract_provider.py`

What `FileExtractProvider` defines:
- `PROVIDER_CODE` — unique provider code in snake_case
- `provider_code()` — returns the provider code
- `provider_title()` — localization key for the settings group title in the UI
- `provider_description()` — settings group description for the UI
- `get_setting(config, key, default)` — read a provider setting from `ExtractConfig`

Required methods implementors must provide:
- `supported_extensions() -> set[str]`
- `project_settings_schema() -> tuple[SettingFieldSchema, ...]`
- `extract(source, config, storage, document_hash) -> ExtractedDocument`

Rules for those methods:
- `supported_extensions()` returns lower-case extensions with a leading dot
- `project_settings_schema()` returns schema fields later localized in the GUI
- `extract(...)` returns only `ExtractedDocument` and persists artifacts via `storage`

## What the provider must return
Minimum valid result:
- `ExtractedDocument.source` with data for the current file
- `ExtractedDocument.extract_hash` equal to the `document_hash` passed into `extract(...)`
- `ExtractedDocument.content` — a list of `ExtractedDocumentContent` items

When there is nothing to extract:
- return `ExtractedDocument(..., content=[])`
- this is valid, e.g. in `skip` mode

## Adding a custom provider
Below is a walkthrough modeled on `src/modules/file_extract/providers/types/text_extract_provider.py`

### 1. Create the provider class
Subclass `FileExtractProvider` and set `PROVIDER_CODE`

```python
class MyFormatExtractProvider(FileExtractProvider):
    PROVIDER_CODE = "my_format_extract_provider"
```

### 2. Declare supported extensions
Implement `supported_extensions()` and return `set[str]`

```python
@staticmethod
def supported_extensions() -> set[str]:
    return {".myext"}
```

### 3. Add the provider settings schema
Implement `project_settings_schema()` using `SettingFieldSchema`

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

### 4. Implement `extract`
The signature is required:

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

Suggested template:
- read provider settings with `self.get_setting(config, "...")`
- handle `skip` and return `content=[]`
- extract content from `source.path_obj()`
- save artifacts with `storage.save_text_content(...)` or equivalent
- build `ExtractedDocumentContent` entries
- return `ExtractedDocument`

### 5. Set `semantic_type` deliberately
- plain text fragment: `SEMANTIC_TYPE_DOCUMENT_FRAGMENT`
- markdown as final markdown fragment: `SEMANTIC_TYPE_MARKDOWN`
- content that needs later recognition: `SEMANTIC_TYPE_REQUIRED_DETECTION`

### 6. Verify the contract
Before wiring the provider in, check:
- `content_type` and `semantic_type` are valid
- `path` points to a cache artifact or is intentionally `None`
- empty results return `ExtractedDocument`, not `None`

## Text provider behavior example
`TextExtractProvider` is the baseline reference:
- supports `.txt`
- exposes `algorithm` with `only_text` and `skip`
- in `skip` mode returns empty `content`
- reads file text as UTF-8
- saves the fragment via `storage.save_text_content(...)`
- returns `ExtractedDocument` with a content list

Use it as the structural template for new formats
