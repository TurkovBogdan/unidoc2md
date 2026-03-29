The path subsystem splits responsibilities across two layers:

- `src/core/app_path.py` — runtime path resolution (`resolve_runtime_root`, `project_root`, `resolve_packaged_assets_data_path`);
- `src/app_path.py` — application `AppPath` dataclass with typed fields (`root`, `logs_dir`) and `AppPath.from_root(...)`.

This keeps low-level directory resolution in `core` and the application path contract in the upper layer.

Key idea: `AppPath` is an extensible core path model. As new core needs appear, add typed fields (e.g. `assets`, `cache`, `temp`) so the rest of the code uses one contract instead of ad hoc path logic.

## `src/app_path.py`

### `AppPath`

Currently a frozen dataclass with two fields:

- `root: Path` — runtime root;
- `logs_dir: Path` — log directory (`root / "logs"`).

```python
from src.app_path import AppPath

paths = AppPath.from_root()
print(paths.root)
print(paths.logs_dir)
```

### `AppPath.from_root(root: Path | None = None) -> AppPath`

Behavior:

- If `root` is passed, use it as the base directory;
- If `root is None`, call `resolve_runtime_root()` from `src.core.app_path`.

The returned object always sets `logs_dir` deterministically to `root / "logs"`.

When extending `AppPath`, compute new fields centrally in `from_root(...)` so path logic stays in one place.

## `src/core/app_path.py`

### `resolve_runtime_root(profile: str | None = None) -> Path`

Runtime root rules:

- Frozen build (`sys.frozen == True`): directory next to the `exe`;
- Source run: `<project_root>/runtime/<profile>`.

`profile` selection:

- explicit `profile` argument if provided;
- else environment variable `APP_PROFILE`;
- if unset, `"dev"`.

```python
from src.core.app_path import resolve_runtime_root

root = resolve_runtime_root()           # default runtime/dev
test_root = resolve_runtime_root("test")
```

### `project_root() -> Path`

Returns the repository root (parent of `src/`), derived from `src/core/app_path.py`.

### `resolve_packaged_assets_data_path(file_name, runtime_root=None) -> Path`

Resolves `assets/data/<file_name>` for the current launch mode:

- source run: `<project_root>/assets/data/<file_name>`;
- frozen onefile: try `sys._MEIPASS/assets/data/<file_name>` first, else `<runtime_root>/assets/data/<file_name>`;
- `runtime_root` may be passed explicitly; otherwise `resolve_runtime_root()` is used.

Contract:

- `file_name` must be a non-empty string or `ValueError`.

## Bootstrap usage

- `CoreBootstrap.core_boot(...)` calls `AppPath.from_root(...)` and prepares `logs_dir`;
- `app_bootstrap(...)` exposes `AppPath` as part of the public startup contract;
- `src/app.py` uses `app_paths.root` as the composition-root `app_root`.

## Usage guidelines

- Prefer `AppPath` (typed fields) over string concatenation for paths.
- Pass `root` explicitly only in tests or isolated scenarios.
- Use `resolve_packaged_assets_data_path(...)` for `assets/data`, not hard-coded paths.
