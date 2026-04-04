# Manual project build
Short guide for installing dependencies, running tests, and building the app

## Requirements
[uv](https://docs.astral.sh/uv/getting-started/installation/) must be installed on your system

## Localization build
Merges UI translation files from the `locale` directory into `assets/locale/`
```shell
# Build localization
uv run python build_locale.py
```

## Dev environment
```shell
# Install dev dependencies
uv sync --extra dev
# Run
uv run python main.py --debug
```

## Running tests
```shell
# Full suite
uv run pytest -v tests
# `core` only
uv run pytest -v tests/core
# `GUI` only
uv run pytest -v tests/gui
# `modules` only
uv run pytest -v tests/modules
```

### Application build
```shell
# Refresh prod dependencies
uv sync
# Install build dependencies
uv sync --extra build
# Build language packs
uv run python build_locale.py
# Build the app for your OS
uv run pyinstaller --clean --distpath dist/release --workpath dist/build urb-app.spec
```
The built app is written to `dist/release/`

## Run configurations
The `.run` folder contains ready-made IDE launch configs for builds and tests

### Build
- `Build - App` — release build via `PyInstaller`
- `Build - Locale` — localization build
- `Run - Dev` — run `main.py --debug`
### Dependencies
- `Sync - Build` — `uv sync --extra build`
- `Sync - Dev` — `uv sync --extra dev`
- `Sync - Prod` — `uv sync`
### Tests
- `Test - Full` — `tests`
- `Test - Core` — `tests/core`
- `Test - GUI` — `tests/gui`
- `Test - Modules` — `tests/modules`
