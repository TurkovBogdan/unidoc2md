# Структура проекта
Карта директорий и ключевой функционал `unidoc2md` с технической точки зрения

## Карта директорий
```text
unidoc2md/
├─ main.py                      # точка входа приложения
├─ app.ini                      # глобальная конфигурация, создается в runtime
├─ build_locale.py              # сборка локализаций из locale/ в assets/locale/
├─ urb-app.spec                 # спецификация PyInstaller для релизной сборки
├─ src/
│  ├─ app.py                    # main_gui/main_cli, запуск сценариев приложения
│  ├─ app_bootstrap.py          # bootstrap модулей и runtime каталогов
│  ├─ app_config.py             # модель глобальной конфигурации app.ini
│  ├─ app_path.py               # пути runtime: projects, cache, logs, assets
│  ├─ core/                     # инфраструктура: конфиг, локали, логирование
│  ├─ gui/                      # интерфейс на Tk и адаптеры
│  └─ modules/
│     ├─ project/               # модель проекта и config.json
│     ├─ project_pipeline/      # оркестратор стадий обработки
│     ├─ file_discovery/        # поиск входных файлов
│     ├─ file_extract/          # извлечение текста из форматов
│     ├─ markdown/              # нормализация markdown и frontmatter
│     ├─ llm_providers/         # клиенты провайдеров LLM
│     ├─ llm_models_registry/   # реестр доступных моделей
│     ├─ yandex_ocr/            # OCR/Vision интеграция
│     └─ settings_schema/       # схемы настроек для UI
├─ tests/
│  ├─ core/                     # тесты инфраструктуры
│  ├─ gui/                      # тесты GUI-слоя
│  └─ modules/                  # тесты модулей и пайплайна
├─ locale/                      # исходники переводов
├─ assets/locale/               # собранные языковые пакеты
├─ docs/                        # документация
└─ .run/                        # run-конфигурации IDE
```

> Описание модуля file_extract: [file-extract-module.md](file-extract-module.md)

## Ключевой функционал
### Вход в приложение и bootstrap
- `main.py` переключает режимы запуска
- `src/app.py` запускает GUI или CLI сценарий
- `src/app_bootstrap.py` поднимает runtime каталоги, конфиг, реестры моделей и провайдеры

### Управление проектами
- `src/modules/project/` хранит модель проекта и секции `config.json`
- В `projects/<name>/docs/` кладутся входные документы
- В `projects/<name>/result/` попадает итоговый markdown

### Конвейер обработки документов
- Оркестратор `PipelineRunner` в `src/modules/project_pipeline/`
- Последовательность стадий:
  - `discovery`
  - `extract`
  - `image_processing`
  - `markdown`
  - `tagging`
  - `result`
- Поддерживается один активный запуск пайплайна и отмена текущего run

### Извлечение и нормализация контента
- `file_discovery` ищет входные файлы по настройкам
- `file_extract` маршрутизирует обработку по типу файла: `pdf`, `office`, `text`, `image`, `markdown`
- `markdown` формирует нормализованный выход для базы знаний и LLM

### Интеграции с LLM и OCR
- `llm_providers` содержит провайдеры `OpenAI`, `Anthropic`, `Google`, `xAI`, `LM Studio`
- `llm_models_registry` хранит и синхронизирует реестр моделей
- `yandex_ocr` отвечает за OCR/Vision сценарии для изображений

### GUI и слой адаптеров
- `src/gui/` содержит экраны, layout и компоненты настроек
- `src/gui/adapters/` связывает UI с модулями домена и конфигурацией
- В UI запускаются пайплайн, валидация и сохранение параметров проекта

### Конфигурация и локализация
- Глобальные настройки лежат в `app.ini`
- Проектные настройки лежат в `projects/<name>/config.json`
- Переводы редактируются в `locale/`, затем собираются командой:

```shell
uv run python build_locale.py
```

> Сборка проекта: [manual-build.md](manual-build.md)
