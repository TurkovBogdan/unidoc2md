"""Классы-обработчики секций конфигурации проекта (умолчания, валидация, доступные значения)."""

from .discovery_config import DiscoveryConfig
from .extract_config import ExtractConfig
from .image_processing_config import (
    IMAGE_PROCESSING_DEFAULTS,
    IMAGE_PROCESSING_KEYS,
    IMAGE_PROCESSING_LOGICS,
    ImageProcessingConfig,
)
from .markdown_config import (
    MARKDOWN_DEFAULTS,
    MARKDOWN_KEYS,
    MARKDOWN_LOGICS,
    MarkdownConfig,
)
from .pipeline_config import PipelineConfig
from .tagging_config import (
    TAGGING_DEFAULTS,
    TAGGING_KEYS,
    TAGGING_LLM_MODES,
    TAGGING_MODES,
    TAGGING_PAYLOAD_LOGIC,
    TAGGING_TAG_FORMAT_VALID,
    TaggingConfig,
)

__all__ = [
    "DiscoveryConfig",
    "ExtractConfig",
    "IMAGE_PROCESSING_DEFAULTS",
    "IMAGE_PROCESSING_KEYS",
    "IMAGE_PROCESSING_LOGICS",
    "ImageProcessingConfig",
    "MARKDOWN_DEFAULTS",
    "MARKDOWN_KEYS",
    "MARKDOWN_LOGICS",
    "MarkdownConfig",
    "PipelineConfig",
    "TAGGING_DEFAULTS",
    "TAGGING_KEYS",
    "TAGGING_LLM_MODES",
    "TAGGING_MODES",
    "TAGGING_PAYLOAD_LOGIC",
    "TAGGING_TAG_FORMAT_VALID",
    "TaggingConfig",
]
