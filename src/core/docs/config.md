Слой конфигурации связывает файл `app.ini` в runtime-корне приложения с типизированной моделью `AppConfig`: ядро отвечает за чтение/запись INI, слияние с дефолтами и единый runtime-store. Полная схема полей приложения (включая секции модулей) задаётся в `src.app_config.AppConfig`; в ядре остаются сервисы доступа к файлу и памяти процесса.

## Boot

Перед чтением настроек из store нужно один раз загрузить или создать `app.ini` относительно runtime root (см. `AppPath`). Без `load_or_create` вызов `AppConfigStore.get()` всё равно валиден: возвращается `AppConfig.default()`, но это не отражает файл на диске.

~~~python
from pathlib import Path

from src.core import AppConfigStore

root = Path("/path/to/runtime")  # или None — авто root как в приложении
cfg = AppConfigStore.load_or_create(root)
print(cfg.core.debug, cfg.core.language)
~~~

Что требуется для запуска:

- каталог runtime (явный `root` или тот же механизм, что в `core_boot`), чтобы знать путь к `app.ini`;
- при первом запуске файл создаётся из `AppConfig.default()`; в существующий файл дописываются недостающие секции и ключи.

## Main services

### `AppConfigStore`

Единая class-based точка доступа к актуальному конфигу в памяти и синхронизации с `app.ini`.

Для чего нужен: после `load_or_create` или `save` любой код может брать один и тот же экземпляр через `get()`.

~~~python
from src.core import AppConfigStore

AppConfigStore.load_or_create()
level = AppConfigStore.get().core.log_level
~~~

Ключевые методы:

- `load_or_create(root=None) -> AppConfig` — создаёт/дополняет `app.ini`, читает, кладёт в store;
- `get() -> AppConfig` — текущий конфиг или `AppConfig.default()`, если store пуст;
- `save(config, root=None)` — пишет `app.ini` и обновляет store;
- `set(config | None)`, `reset()` — смена/сброс in-memory без обязательной записи на диск.

### `AppConfigBuilder`

Опциональная обёртка над низкоуровневой загрузкой с фиксированным `root`: `build()` эквивалентен `load_or_create(self._root)` из `app_config_builder`, **без** обновления `AppConfigStore`.

~~~python
from pathlib import Path

from src.core import AppConfigBuilder

builder = AppConfigBuilder(Path("/path/to/runtime"))
cfg = builder.build()
~~~

Когда использовать: тесты или сценарии, где нужен `AppConfig` с диска, но не глобальный store.

### `load_or_create` / `save_config` (`src.core.app_config_builder`)

Публичные функции уровня файла: читают/пишут `app.ini` по `AppPath.from_root(root).app_ini`, **не** трогая `AppConfigStore`. Для прикладного кода предпочтительнее `AppConfigStore`.

~~~python
from src.core.app_config_builder import load_or_create, save_config
from src.app_config import AppConfig

cfg = load_or_create()
save_config(cfg)
~~~

### Константа `INI_FILENAME`

В модуле объявлена строка `"app.ini"`; фактический путь задаётся через `AppPath`, а не только имя файла.

## Models

### `AppConfig` (`src.app_config`)

Назначение: корневая frozen-модель всего `app.ini`: одно поле на INI-секцию (имя секции — верхний регистр имени поля, например `core` → `[CORE]`, `llm_providers` → `[LLM_PROVIDERS]`).

- `core`: `CoreConfig` — отладка, уровни логов, язык UI;
- `llm_providers`: `LLMProvidersConfig` — флаги провайдеров, ключи API, таймаут;
- `yandex_ocr`: `YandexOCRConfig` — включение Yandex OCR и учётные данные.

~~~python
from src.app_config import AppConfig

cfg = AppConfig.default()
assert cfg.core.debug is False
~~~

### `CoreConfig` (`src.core.models.core_config`)

Назначение: только секция `[CORE]`.

| Поле | Тип | INI-ключ | Смысл |
|------|-----|----------|--------|
| `debug` | `bool` | `DEBUG` | режим отладки |
| `log_level` | `str` | `LEVEL` | уровень файлового лога |
| `console_log_level` | `str` | `CONSOLE_LEVEL` | уровень консольного лога |
| `language` | `str` | `LANGUAGE` | код языка (пусто — по умолчанию приложения) |

### `LLMProvidersConfig` / `YandexOCRConfig`

Назначение: поля секций `[LLM_PROVIDERS]` и `[YANDEX_OCR]` в том виде, в каком их сериализует `app_config_builder` (имена ключей в INI совпадают с именами полей dataclass в верхнем регистре, если не задано `metadata["ini_key"]`). Поведение провайдеров и вспомогательные методы (`is_provider_available`, `is_available`) описаны в соответствующих модулях.

## Exceptions

Выделенного набора исключений у слоя конфигурации нет: при проблемах с диском возможны стандартные исключения Python (`OSError` и т.п.). Некорректные или неполные значения в INI при чтении подменяются дефолтами из `AppConfig.default()` для соответствующих полей.
