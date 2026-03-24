Подсистема локализации ядра даёт единый способ получать переведённые строки из JSON-каталогов по ключу сообщения (как у gettext), синхронизировать каталоги с runtime-каталогом и согласовать активный язык с секцией `[CORE]` в `app.ini`.

Контракт для приложения: один язык = один файл `assets/locale/<код>.json`.

## Boot

Локализация не работает, пока не зарегистрирован список языков и не скопированы файлы каталогов в `assets/locale` под корнем runtime. В приложении это делает `CoreBootstrap.lang_boot` сразу после `CoreBootstrap.core_boot`, который загружает конфиг в `AppConfigStore`.

```python
from pathlib import Path

from src.core import AppConfigStore
from src.core.bootstrap import CoreBootstrap

paths = CoreBootstrap.core_boot(None)  # или Path к корню runtime
CoreBootstrap.lang_boot(
    paths,
    {
        "ru": "Русский",
        "en": "English",
        "zh": "中文",
    },
)
# Если в app.ini [CORE] LANGUAGE задан валидный код — активный язык уже применён.
```

Что требуется для запуска:

- В репозитории (или в bundle PyInstaller) должны лежать файлы `assets/locale/<код>.json` для каждого ключа из переданного словаря языков.
- `lang_boot` копирует их в `<paths.root>/assets/locale/` (если источник и приёмник не совпадают).
- Сохранённый язык читается из `AppConfigStore.get().core.language` (ключ `LANGUAGE` в секции `[CORE]`); пустое или неизвестное значение означает, что язык нужно выбрать в UI — см. `language_choice_required`.

Минимальный сценарий без полного GUI: после `lang_boot` можно вызывать `locmsg("some.key")`; при необходимости сменить язык — `set_language("en")`.

## Main services

### `AVAILABLE_LANGUAGES`

Для чего нужен: отображаемые подписи языков в настройках или экране выбора языка; ключи словаря — нормализованные коды (`en`, `ru`, `zh_CN` → `zh_cn` при регистрации через внутренний normalize).

```python
from src.core import AVAILABLE_LANGUAGES

for code, label in AVAILABLE_LANGUAGES.items():
    print(code, label)
```

Заполняется только вызовом `CoreBootstrap.lang_boot(..., available_languages=...)`. До boot словарь пустой.

### `set_language`

Когда использовать: смена языка во время работы приложения (например, после выбора в настройках); перед сохранением нового значения в конфиг обычно обновляют `app.ini` через существующий механизм конфигурации приложения.

```python
from src.core import set_language

set_language("en")
```

Ограничения: код языка должен быть одним из ключей `AVAILABLE_LANGUAGES`; иначе `ValueError`.

### `language_choice_required`

Когда использовать: решить, показывать ли пользователю экран/диалог выбора языка при старте.

```python
from src.core import language_choice_required

if language_choice_required():
    # показать выбор языка
    ...
```

Возвращает `True`, если в `AppConfigStore` поле `core.language` пустое или не входит в `AVAILABLE_LANGUAGES`.

### `locmsg`

Для чего нужен: короткий алиас перевода строки по ключу-сообщению (идентично `gettext` для текущего языка).

```python
from src.core import locmsg

title = locmsg("app.title")
```

Успешный результат: строка из JSON-каталога для активного языка; если ключа нет — возвращается исходный ключ (fallback).

Требования: должен быть выполнен boot локализации и установлен валидный активный язык (`lang_boot` или `set_language`). Иначе возможен `ValueError`. Если файл каталога для языка отсутствует или имеет неверный формат, при первом обращении к переводу возможны `FileNotFoundError` или `ValueError` из загрузчика каталога.

## Models

### Каталог локали (JSON)

Назначение: плоский словарь «ключ сообщения → переведённая строка» для одного языка.

| Поле (ключ JSON) | Тип | Смысл |
|------------------|-----|--------|
| произвольный `str` | `str` | Текст перевода; ключ часто в виде `domain.fragment` (например `error.project_not_found`) |

Итоговый файл рантайма: `assets/locale/<код>.json`, где `<код>` совпадает с нормализованным кодом языка (регистр не важен при вводе, внутри приводится к нижнему регистру, `-` заменяется на `_`).

```json
{
  "app.title": "unidoc2md",
  "error.project_not_found": "Project not found"
}
```

### Регистрация доступных языков

Назначение: аргумент `available_languages` в `CoreBootstrap.lang_boot`.

| Поле | Тип | Смысл |
|------|-----|--------|
| ключ | `str` | Код языка (после нормализации — ключ в `AVAILABLE_LANGUAGES` и имя файла `{code}.json`) |
| значение | `str` | Человекочитаемое имя для UI (не пустая строка) |

```python
CoreBootstrap.lang_boot(
    paths,
    {"ru": "Русский", "en": "English"},
)
```

### `CoreConfig.language` (фрагмент `app.ini`)

Назначение: сохранённый предпочитаемый язык пользователя.

| Поле | Тип | Смысл |
|------|-----|--------|
| `language` | `str` | Код из `[CORE] LANGUAGE`; пусто или невалидное значение ведёт к `language_choice_required() == True` |

Пример в `app.ini`:

```ini
[CORE]
LANGUAGE = en
```

## Exceptions

Отдельной иерархии исключений модуль не определяет; в контракт входят стандартные исключения Python в предсказуемых ситуациях.

| Exception | When raised |
|-----------|-------------|
| `ValueError` | Пустой словарь языков при регистрации; пустое имя языка; попытка `set_language` с кодом не из `AVAILABLE_LANGUAGES`; активный язык не задан или невалиден при запросе перевода; JSON каталога не объект или не все пары строка–строка |
| `FileNotFoundError` | Отсутствует файл `assets/locale/<код>.json` для запрошенного языка |

```python
from src.core import set_language

try:
    set_language("de")
except ValueError:
    # код не зарегистрирован в AVAILABLE_LANGUAGES
    pass
```
