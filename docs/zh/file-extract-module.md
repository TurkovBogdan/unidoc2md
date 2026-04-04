# `file_extract` 模块
本模块负责从文件中提取内容，并将结果统一到单一契约，供后续流水线阶段使用

## 模块目录结构
```text
src/modules/file_extract/
├─ __init__.py
├─ README.md
├─ bootstrap.py
├─ module.py
├─ interfaces/
│  └─ file_extract_provider.py
├─ models/
│  ├─ extract_config.py
│  ├─ extracted_document.py
│  └─ source_document.py
├─ providers/
│  ├─ file_extract_provider.py
│  ├─ providers_registry.py
│  └─ types/
│     ├─ text_extract_provider.py
│     ├─ markdown_extract_provider.py
│     ├─ image_extract_provider.py
│     ├─ pdf_extract/
│     └─ office_extract/
├─ schemas/
│  ├─ provider_config_builder.py
│  └─ provider_schema_builder.py
└─ services/
   ├─ file_extract_service.py
   └─ file_extract_cache.py
```

## 顶层设计
- 模块输入：`SourceDocument` 与运行时配置 `ExtractConfig`
- `FileExtractService` 按文件扩展名选择提供者
- 缓存键为 `compute_extract_hash(config, file_hash)`
- 若已有缓存结果，直接返回缓存版本
- 若无缓存，执行 `provider.extract(...)`，持久化后以 `ExtractedDocument` 返回

关键路径：
- 服务：`src/modules/file_extract/services/file_extract_service.py`
- 提供者接口：`src/modules/file_extract/interfaces/file_extract_provider.py`
- 模型：`src/modules/file_extract/models/`

## 提供者结果契约
每个提供者必须返回 `ExtractedDocument` 实例

`ExtractedDocument` 字段：
- `source` — 源文档元数据，类型为 `DiscoveredDocument`
- `config` — 实际使用的 `ExtractConfig`
- `extract_hash` — 该文档的缓存键哈希
- `content_hash` — 聚合内容的可选哈希
- `content` — `ExtractedDocumentContent` 条目列表

`ExtractedDocumentContent` 字段：
- `content_type` — 载体类型：`text`、`image`、`markdown`
- `semantic_type` — 片段语义角色：
  - `document_fragment`
  - `required_detection`
  - `markdown`
- `path` — 缓存中产物路径，或 `None`
- `mime_type` — 已知时的 MIME 类型
- `content_hash` — 已计算时的内容哈希
- `value` — 本阶段若需要则携带的 payload

实践规则：
- 提供者不得返回原始任意格式
- 提供者仅返回已正确填充 `content` 的 `ExtractedDocument`

## 提供者接口
基类接口位于 `src/modules/file_extract/interfaces/file_extract_provider.py`

`FileExtractProvider` 约定：
- `PROVIDER_CODE` — snake_case 的唯一提供者代码
- `provider_code()` — 返回提供者代码
- `provider_title()` — 界面中设置分组标题的本地化键
- `provider_description()` — 界面中设置分组描述
- `get_setting(config, key, default)` — 从 `ExtractConfig` 读取提供者设置

实现方必须实现的方法：
- `supported_extensions() -> set[str]`
- `project_settings_schema() -> tuple[SettingFieldSchema, ...]`
- `extract(source, config, storage, document_hash) -> ExtractedDocument`

上述方法的规则：
- `supported_extensions()` 返回小写且带前导点的扩展名
- `project_settings_schema()` 返回后续在 GUI 中本地化的模式字段
- `extract(...)` 仅返回 `ExtractedDocument`，并通过 `storage` 持久化产物

## 提供者必须返回的内容
最小合法结果：
- `ExtractedDocument.source` 含当前文件数据
- `ExtractedDocument.extract_hash` 等于传入 `extract(...)` 的 `document_hash`
- `ExtractedDocument.content` — `ExtractedDocumentContent` 条目列表

无可提取内容时：
- 返回 `ExtractedDocument(..., content=[])`
- 合法场景，例如 `skip` 模式

## 添加自定义提供者
以下流程以 `src/modules/file_extract/providers/types/text_extract_provider.py` 为范本

### 1. 创建提供者类
继承 `FileExtractProvider` 并设置 `PROVIDER_CODE`

```python
class MyFormatExtractProvider(FileExtractProvider):
    PROVIDER_CODE = "my_format_extract_provider"
```

### 2. 声明支持的扩展名
实现 `supported_extensions()` 并返回 `set[str]`

```python
@staticmethod
def supported_extensions() -> set[str]:
    return {".myext"}
```

### 3. 添加提供者设置模式
使用 `SettingFieldSchema` 实现 `project_settings_schema()`

```python
@classmethod
def project_settings_schema(cls) -> tuple[SettingFieldSchema, ...]:
    return (
        SettingFieldSchema(
            key="algorithm",
            type="select",
            default="default_mode",
            label="algorithm",
            description="",
            options=(("default_mode", "default_mode"), ("skip", "skip")),
        ),
    )
```

### 4. 实现 `extract`
签名固定：

```python
def extract(
    self,
    source: SourceDocument,
    config: ExtractConfig,
    storage: FileExtractCacheService,
    document_hash: str,
) -> ExtractedDocument:
    ...
```

推荐步骤：
- 用 `self.get_setting(config, "...")` 读取提供者设置
- 处理 `skip` 并返回 `content=[]`
- 从 `source.path_obj()` 提取内容
- 通过 `storage.save_text_content(...)` 或同类 API 保存产物
- 组装 `ExtractedDocumentContent`
- 返回 `ExtractedDocument`

### 5. 明确设置 `semantic_type`
- 普通文本片段：`SEMANTIC_TYPE_DOCUMENT_FRAGMENT`
- 作为最终 Markdown 片段：`SEMANTIC_TYPE_MARKDOWN`
- 需后续识别的内容：`SEMANTIC_TYPE_REQUIRED_DETECTION`

### 6. 校验契约
接入前请确认：
- `content_type` 与 `semantic_type` 合法
- `path` 指向缓存产物，或有意为 `None`
- 空结果返回 `ExtractedDocument`，而非 `None`

## 文本提供者行为示例
`TextExtractProvider` 可作为基准参考：
- 支持 `.txt`
- 提供 `algorithm`，含 `only_text` 与 `skip`
- `skip` 模式下返回空 `content`
- 以 UTF-8 读取文件文本
- 通过 `storage.save_text_content(...)` 保存片段
- 返回带内容列表的 `ExtractedDocument`

新增格式时可按其结构仿写
