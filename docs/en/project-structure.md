# Project structure
Directory map and main `unidoc2md` functionality from a technical perspective

## Directory map
```text
unidoc2md/
├─ main.py                      # application entry point
├─ app.ini                      # global config, created at runtime
├─ build_locale.py              # build locales from locale/ to assets/locale/
├─ urb-app.spec                 # PyInstaller spec for release builds
├─ src/
│  ├─ app.py                    # main_gui/main_cli, app scenario entry
│  ├─ app_bootstrap.py          # module bootstrap and runtime directories
│  ├─ app_config.py             # global app.ini configuration model
│  ├─ app_path.py               # runtime paths: projects, cache, logs, assets
│  ├─ core/                     # infrastructure: config, locales, logging
│  ├─ gui/                      # Tk UI and adapters
│  └─ modules/
│     ├─ project/               # project model and config.json
│     ├─ project_pipeline/      # processing stage orchestrator
│     ├─ file_discovery/        # input file discovery
│     ├─ file_extract/          # text extraction by format
│     ├─ markdown/              # markdown and frontmatter normalization
│     ├─ llm_providers/         # LLM provider clients
│     ├─ llm_models_registry/   # available model registry
│     ├─ yandex_ocr/            # OCR/Vision integration
│     └─ settings_schema/       # UI setting schemas
├─ tests/
│  ├─ core/                     # infrastructure tests
│  ├─ gui/                      # GUI layer tests
│  └─ modules/                  # module and pipeline tests
├─ locale/                      # translation sources
├─ assets/locale/               # built language packs
├─ docs/                        # documentation
└─ .run/                        # IDE run configurations
```

> `file_extract` module: [file-extract-module.md](file-extract-module.md)

## Key functionality
### App entry and bootstrap
- `main.py` selects launch mode
- `src/app.py` runs the GUI or CLI scenario
- `src/app_bootstrap.py` sets up runtime directories, config, model registries, and providers

### Project management
- `src/modules/project/` holds the project model and `config.json` sections
- Input documents go in `projects/<name>/docs/`
- Final markdown lands in `projects/<name>/result/`

### Document processing pipeline
- Orchestrator `PipelineRunner` in `src/modules/project_pipeline/`
- Stage order:
  - `discovery`
  - `extract`
  - `image_processing`
  - `markdown`
  - `tagging`
  - `result`
- One active pipeline run at a time; the current run can be cancelled

### Content extraction and normalization
- `file_discovery` finds input files per settings
- `file_extract` routes by file type: `pdf`, `office`, `text`, `image`, `markdown`
- `markdown` produces normalized output for knowledge bases and LLMs

### LLM and OCR integrations
- `llm_providers` includes `OpenAI`, `Anthropic`, `Google`, `xAI`, `LM Studio`
- `llm_models_registry` stores and syncs the model registry
- `yandex_ocr` covers OCR/Vision flows for images

### GUI and adapter layer
- `src/gui/` contains screens, layouts, and settings components
- `src/gui/adapters/` connects the UI to domain modules and configuration
- The UI drives the pipeline, validation, and saving project parameters

### Configuration and localization
- Global settings live in `app.ini`
- Project settings live in `projects/<name>/config.json`
- Edit translations in `locale/`, then build with:

```shell
uv run python build_locale.py
```

> Building the project: [manual-build.md](manual-build.md)
