# Ручная сборка проекта
Краткая инструкция по установке зависимостей, запуску тестов и сборке приложения

## Требования
В системе должен быть [установлен uv](https://docs.astral.sh/uv/getting-started/installation/)

## Сборка локализации
Объединяет файлы перевода интерфейса из директории `locale` в `/assets/locale/`
```shell
# Собираем локализацию
uv run python build_locale.py
```

## Запуск dev-окружения
```shell
# Ставим dev-зависимости 
uv sync --extra dev
# Запуск
uv run python main.py --debug
```

## Запуск тестов
```shell
# Полный набор
uv run pytest -v tests
# Только `core`
uv run pytest -v tests/core
# Только `GUI`
uv run pytest -v tests/gui
# Только `modules`
uv run pytest -v tests/modules
```

### Сборка приложения
```shell
# Обновляем prod-зависимости
uv sync
# Ставим build-зависимости
uv sync --extra build
# Собираем языковые пакеты
uv run python build_locale.py
# Собираем приложение под систему
uv run pyinstaller --clean --distpath dist/release --workpath dist/build urb-app.spec
```
Собранное приложение сохранится в `dist/release/`

## run-конфигурации
В папке `.run` находятся готовые конфигурации для запуска сборки/тестов из IDE

### Сборка
- `Build - App` — релизная сборка через `PyInstaller`
- `Build - Locale` — сборка локалей
- `Run - Dev` — запуск `main.py --debug`
### Зависимости
- `Sync - Build` — `uv sync --extra build`
- `Sync - Dev` — `uv sync --extra dev`
- `Sync - Prod` — `uv sync`
### Тесты
- `Test - Full` — `tests` 
- `Test - Core` — `tests/core`
- `Test - GUI` — `tests/gui`
- `Test - Modules` — `tests/modules`