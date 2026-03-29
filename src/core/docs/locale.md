The core localization subsystem provides one way to resolve translated strings from JSON catalogs by message key (gettext-style), sync catalogs into the runtime tree, and align the active language with the `[CORE]` section in `app.ini`.

Application contract: one language = one file `assets/locale/<code>.json`.

## Boot

Localization is inactive until languages are registered and catalog files are copied under `<runtime>/assets/locale`. The app does this with `CoreBootstrap.lang_boot` right after `CoreBootstrap.core_boot`, which loads config into `AppConfigStore`.

```python
from pathlib import Path

from src.core import AppConfigStore
from src.core.bootstrap import CoreBootstrap

paths = CoreBootstrap.core_boot(None)  # or Path to runtime root
CoreBootstrap.lang_boot(
    paths,
    {
        "ru": "Russian",
        "en": "English",
        "zh": "Chinese",
    },
)
# If app.ini [CORE] LANGUAGE is a valid code, the active language is already applied.
```

Startup requirements:

- `assets/locale/<code>.json` must exist in the repo (or PyInstaller bundle) for every key in the passed language map.
- `lang_boot` copies them to `<paths.root>/assets/locale/` when source and target differ.
- Saved language is read from `AppConfigStore.get().core.language` (`LANGUAGE` in `[CORE]`); empty or unknown means the UI should prompt — see `language_choice_required`.

Minimal flow without full GUI: after `lang_boot`, call `locmsg("some.key")`; to switch language, `set_language("en")`.

## Main services

### `AVAILABLE_LANGUAGES`

Purpose: human-readable language labels for settings or a language picker; dict keys are normalized codes (`en`, `ru`, `zh_CN` → `zh_cn` when registered via internal normalization).

```python
from src.core import AVAILABLE_LANGUAGES

for code, label in AVAILABLE_LANGUAGES.items():
    print(code, label)
```

Populated only by `CoreBootstrap.lang_boot(..., available_languages=...)`. Before boot the dict is empty.

### `set_language`

When to use: change language while the app is running (e.g. after a settings choice).

```python
from src.core import set_language

set_language("en")
```

What the call does:

- validates and sets the active language in the runtime store;
- persists the code to `app.ini` via `AppConfigStore.save(...)` (`[CORE] LANGUAGE`);
- notifies language-change listeners if the code actually changed.

Constraint: the code must be a key of `AVAILABLE_LANGUAGES`; otherwise `ValueError`.

### `add_language_change_listener` / `remove_language_change_listener`

When to use: let UI/modules react to language changes without polling.

```python
from src.core import (
    add_language_change_listener,
    remove_language_change_listener,
    set_language,
)

def on_language_changed(old_language: str, new_language: str) -> None:
    # e.g. refresh titles/menus
    ...

add_language_change_listener(on_language_changed)
set_language("ru")
remove_language_change_listener(on_language_changed)
```

Event contract:

- callback signature: `listener(old_language: str, new_language: str)`;
- fired only on an actual code change (`en -> ru`, not `en -> en`);
- registering the same callback twice is ignored;
- removing an unregistered callback is safe.

### `language_choice_required`

When to use: decide whether to show a language picker at startup.

```python
from src.core import language_choice_required

if language_choice_required():
    # show language selection
    ...
```

Returns `True` if `AppConfigStore` has `core.language` empty or not in `AVAILABLE_LANGUAGES`.

### `locmsg`

Purpose: short alias to translate a string by message key (same idea as gettext for the current language).

```python
from src.core import locmsg

title = locmsg("app.title")
```

On success: string from the JSON catalog for the active language; if the key is missing, the key is returned (fallback).

Requirements: localization boot must have run and a valid active language must be set (`lang_boot` or `set_language`). Otherwise `ValueError` is possible. If the catalog file is missing or malformed, the first translation access may raise `FileNotFoundError` or `ValueError` from the loader.

## Models

### Locale catalog (JSON)

Purpose: flat map “message key → translated string” for one language.

| JSON key | Type | Meaning |
|----------|------|---------|
| any `str` | `str` | Translated text; keys often look like `domain.fragment` (e.g. `error.project_not_found`) |

Runtime file: `assets/locale/<code>.json` where `<code>` matches the normalized language code (input casing ignored; internally lowercased, `-` → `_`).

```json
{
  "app.title": "unidoc2md",
  "error.project_not_found": "Project not found"
}
```

### Registering available languages

Purpose: `available_languages` argument to `CoreBootstrap.lang_boot`.

| Field | Type | Meaning |
|-------|------|---------|
| key | `str` | Language code (after normalization: key in `AVAILABLE_LANGUAGES` and `{code}.json` filename) |
| value | `str` | Human-readable label for the UI (non-empty) |

```python
CoreBootstrap.lang_boot(
    paths,
    {"ru": "Russian", "en": "English"},
)
```

### `CoreConfig.language` (`app.ini` fragment)

Purpose: persisted user-preferred language.

| Field | Type | Meaning |
|-------|------|---------|
| `language` | `str` | Code from `[CORE] LANGUAGE`; empty or invalid yields `language_choice_required() == True` |

Example `app.ini`:

```ini
[CORE]
LANGUAGE = en
```

## Exceptions

The module does not define a custom hierarchy; standard Python exceptions apply in predictable situations.

| Exception | When raised |
|-----------|-------------|
| `ValueError` | Empty language map on registration; empty display name; `set_language` with unknown code; active language missing/invalid on translate; catalog JSON not an object or not all string pairs |
| `FileNotFoundError` | Missing `assets/locale/<code>.json` for the requested language |
| Any subscriber exception | Propagates from the language-change callback to the `set_language(...)` caller |

```python
from src.core import set_language

try:
    set_language("de")
except ValueError:
    # code not registered in AVAILABLE_LANGUAGES
    pass
```
