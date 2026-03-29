The configuration layer ties `app.ini` under the application runtime root to the typed `AppConfig` model: the core handles INI read/write, merging with defaults, and a single runtime store. The full application field schema (including module sections) lives in `src.app_config.AppConfig`; the core provides file access and in-process store services.

## Boot

Before reading settings from the store, load or create `app.ini` once relative to the runtime root (see `src.app_path.AppPath`). Without `load_or_create`, `AppConfigStore.get()` is still valid: it returns `AppConfig.default()`, but that does not reflect the file on disk.

~~~python
from pathlib import Path

from src.core import AppConfigStore

root = Path("/path/to/runtime")  # or None — auto root like the app
cfg = AppConfigStore.load_or_create(root)
print(cfg.core.debug, cfg.core.language)
~~~

Startup requirements:

- a runtime directory (explicit `root` or the same mechanism as `core_boot`) so the path to `app.ini` is known;
- on first run the file is created from `AppConfig.default()`; missing sections and keys are appended to an existing file.

## Main services

### `AppConfigStore`

Single class-based access to the in-memory config and synchronization with `app.ini`.

Purpose: after `load_or_create` or `save`, any code can share one instance via `get()`.

~~~python
from src.core import AppConfigStore

AppConfigStore.load_or_create()
level = AppConfigStore.get().core.log_level
~~~

Key methods:

- `load_or_create(root=None) -> AppConfig` — create/merge `app.ini`, read, store;
- `get() -> AppConfig` — current config or `AppConfig.default()` if the store is empty;
- `save(config, root=None)` — write `app.ini` and update the store;
- `set(config | None)`, `reset()` — change/clear in-memory state without a required disk write.

### `AppConfigBuilder`

Optional wrapper over low-level load with a fixed `root`: `build()` equals `load_or_create(self._root)` from `app_config_builder`, **without** updating `AppConfigStore`.

~~~python
from pathlib import Path

from src.core import AppConfigBuilder

builder = AppConfigBuilder(Path("/path/to/runtime"))
cfg = builder.build()
~~~

When to use: tests or flows that need `AppConfig` from disk but not the global store.

### `load_or_create` / `save_config` (`src.core.app_config_builder`)

File-level helpers: read/write `app.ini` at the runtime root (`root / "app.ini"` or `resolve_runtime_root() / "app.ini"`), **without** touching `AppConfigStore`. Application code should prefer `AppConfigStore`.

~~~python
from src.core.app_config_builder import load_or_create, save_config
from src.app_config import AppConfig

cfg = load_or_create()
save_config(cfg)
~~~

### Constant `INI_FILENAME`

The module defines the string `"app.ini"`; the real path is resolved via `AppPath`, not the bare filename alone.

## Models

### `AppConfig` (`src.app_config`)

Purpose: root frozen model of the whole `app.ini`: one field per INI section (section name is the uppercased field name, e.g. `core` → `[CORE]`).

The current template defines only the core section:

- `core`: `CoreConfig` — debug, log levels, UI language.

~~~python
from src.app_config import AppConfig

cfg = AppConfig.default()
assert cfg.core.debug is False
~~~

### `CoreConfig` (`src.core.models.core_config`)

Purpose: the `[CORE]` section only.

| Field | Type | INI key | Meaning |
|------|-----|---------|---------|
| `debug` | `bool` | `DEBUG` | debug mode |
| `log_level` | `str` | `LEVEL` | file log level |
| `console_log_level` | `str` | `CONSOLE_LEVEL` | console log level |
| `language` | `str` | `LANGUAGE` | language code (empty — app default) |

Add new sections via `src.app_config.AppConfig` and `AppConfig.default()`. After that, `AppConfigStore.load_or_create()` will create/merge the matching sections and keys in `app.ini`.

## Exceptions

There is no dedicated exception hierarchy for this layer: disk issues surface as standard Python exceptions (`OSError`, etc.). Invalid or incomplete INI values on read are replaced with defaults from `AppConfig.default()` for the affected fields.
