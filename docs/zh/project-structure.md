# 项目结构
从技术角度梳理 `unidoc2md` 的目录布局与核心能力

## 目录一览
```text
unidoc2md/
├─ main.py                      # 应用入口
├─ app.ini                      # 全局配置，运行时生成
├─ build_locale.py              # 从 locale/ 构建到 assets/locale/
├─ urb-app.spec                 # PyInstaller 发布构建规格
├─ src/
│  ├─ app.py                    # main_gui/main_cli，应用场景入口
│  ├─ app_bootstrap.py          # 模块引导与运行时目录
│  ├─ app_config.py             # 全局 app.ini 配置模型
│  ├─ app_path.py               # 运行时路径：projects、cache、logs、assets
│  ├─ core/                     # 基础设施：配置、本地化、日志
│  ├─ gui/                      # Tk 界面与适配层
│  └─ modules/
│     ├─ project/               # 项目模型与 config.json
│     ├─ project_pipeline/      # 处理阶段编排
│     ├─ file_discovery/        # 发现输入文件
│     ├─ file_extract/          # 按格式提取文本
│     ├─ markdown/              # Markdown 与 frontmatter 规范化
│     ├─ llm_providers/         # LLM 提供商客户端
│     ├─ llm_models_registry/   # 可用模型注册表
│     ├─ yandex_ocr/            # OCR/Vision 集成
│     └─ settings_schema/       # 界面设置模式
├─ tests/
│  ├─ core/                     # 基础设施测试
│  ├─ gui/                      # GUI 层测试
│  └─ modules/                  # 模块与流水线测试
├─ locale/                      # 翻译源文件
├─ assets/locale/               # 构建后的语言包
├─ docs/                        # 文档
└─ .run/                        # IDE 运行配置
```

> `file_extract` 模块说明：[file-extract-module.md](file-extract-module.md)

## 核心功能
### 应用入口与引导
- `main.py` 选择启动模式
- `src/app.py` 运行 GUI 或 CLI 场景
- `src/app_bootstrap.py` 初始化运行时目录、配置、模型注册表与各类提供商

### 项目管理
- `src/modules/project/` 保存项目模型与 `config.json` 各节
- 输入文档放在 `projects/<name>/docs/`
- 最终 Markdown 输出到 `projects/<name>/result/`

### 文档处理流水线
- 编排器 `PipelineRunner` 位于 `src/modules/project_pipeline/`
- 阶段顺序：
  - `discovery`
  - `extract`
  - `image_processing`
  - `markdown`
  - `tagging`
  - `result`
- 同一时间仅一个流水线运行；可取消当前运行

### 内容提取与规范化
- `file_discovery` 按设置查找输入文件
- `file_extract` 按文件类型路由：`pdf`、`office`、`text`、`image`、`markdown`
- `markdown` 生成面向知识库与 LLM 的规范化输出

### LLM 与 OCR 集成
- `llm_providers` 包含 `OpenAI`、`Anthropic`、`Google`、`xAI`、`LM Studio`
- `llm_models_registry` 存储并同步模型注册表
- `yandex_ocr` 负责图像的 OCR/Vision 流程

### GUI 与适配层
- `src/gui/` 包含界面、布局与设置组件
- `src/gui/adapters/` 将界面与领域模块及配置连接
- 界面驱动流水线、校验与项目参数保存

### 配置与本地化
- 全局设置位于 `app.ini`
- 项目设置位于 `projects/<name>/config.json`
- 在 `locale/` 编辑翻译后执行：

```shell
uv run python build_locale.py
```

> 项目构建：[manual-build.md](manual-build.md)
