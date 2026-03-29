"""Adapters between GUI and backend calls."""

from .backend import (
    ProjectInfo,
    create_project,
    load_projects,
    remove_project,
    load_project_config_dict,
    save_project_config_dict,
    validate_config,
    get_api_token_status,
    load_app_config_dict,
    save_app_config_dict,
)
from .llm_models import (
    LLMModelsAdapter,
    LLMProviderModelRecord,
    SyncReport,
    get_llm_models_adapter,
)
from .registry_options import (
    get_chat_models_for_provider,
    get_chat_provider_options,
    get_ocr_models_for_provider,
    get_ocr_provider_options,
    get_vision_models_for_provider,
    get_vision_provider_options,
)

__all__ = [
    "ProjectInfo",
    "create_project",
    "load_projects",
    "remove_project",
    "load_project_config_dict",
    "save_project_config_dict",
    "validate_config",
    "get_api_token_status",
    "load_app_config_dict",
    "save_app_config_dict",
    "LLMModelsAdapter",
    "LLMProviderModelRecord",
    "SyncReport",
    "get_llm_models_adapter",
    "get_chat_models_for_provider",
    "get_chat_provider_options",
    "get_ocr_provider_options",
    "get_ocr_models_for_provider",
    "get_vision_provider_options",
    "get_vision_models_for_provider",
]
