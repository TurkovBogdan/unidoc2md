# 手动构建项目
简要说明：安装依赖、运行测试与打包应用

## 环境要求
系统中需已[安装 uv](https://docs.astral.sh/uv/getting-started/installation/)

## 构建界面本地化
将 `locale` 目录下的界面翻译文件合并到 `assets/locale/`
```shell
# 构建本地化资源
uv run python build_locale.py
```

## 开发环境
```shell
# 安装开发依赖
uv sync --extra dev
# 运行
uv run python main.py --debug
```

## 运行测试
```shell
# 全部测试
uv run pytest -v tests
# 仅 core
uv run pytest -v tests/core
# 仅 GUI
uv run pytest -v tests/gui
# 仅 modules
uv run pytest -v tests/modules
```

### 打包应用
```shell
# 同步生产依赖
uv sync
# 安装构建依赖
uv sync --extra build
# 构建语言包
uv run python build_locale.py
# 为当前系统打包
uv run pyinstaller --clean --distpath dist/release --workpath dist/build urb-app.spec
```
构建产物位于 `dist/release/`

## 运行配置
`.run` 目录包含可在 IDE 中直接使用的构建/测试启动配置

### 构建
- `Build - App` — 通过 `PyInstaller` 发布构建
- `Build - Locale` — 构建本地化
- `Run - Dev` — 运行 `main.py --debug`
### 依赖
- `Sync - Build` — `uv sync --extra build`
- `Sync - Dev` — `uv sync --extra dev`
- `Sync - Prod` — `uv sync`
### 测试
- `Test - Full` — `tests`
- `Test - Core` — `tests/core`
- `Test - GUI` — `tests/gui`
- `Test - Modules` — `tests/modules`
