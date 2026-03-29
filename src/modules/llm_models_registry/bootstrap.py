"""llm_models_registry bootstrap: merge bundled registry into the user file."""

from __future__ import annotations

from pathlib import Path

from .boot import LLMModelStoreMerger
from .module import ModuleConfig, ModuleConfigStore
from .providers.llm_model_store import bind_llm_model_store, reset_llm_model_store


def module_llm_model_registry_boot(
    source_llm_models_store_file: Path | str,
    user_llm_models_store_file: Path | str,
) -> None:
    """
    Ensure the user registry file exists (flat JSON object: keys ``provider@name`` → record).
    ``source_llm_models_store_file`` — bundled canonical registry (source).
    ``user_llm_models_store_file`` — user registry path (written).
    If the user file already exists: add models from source that are missing in the target;
    overwrite an entry only when the target still allows service updates
    (``target.can_update=true``). After manual edits set ``can_update=false`` so bootstrap
    skips that row.
    """
    source_file = Path(source_llm_models_store_file).resolve()
    user_file = Path(user_llm_models_store_file).resolve()
    user_file.parent.mkdir(parents=True, exist_ok=True)
    config = ModuleConfig(models_store_file=user_file)
    ModuleConfigStore.set(config)
    reset_llm_model_store()
    LLMModelStoreMerger.apply_boot_merge(source_file, user_file)
    bind_llm_model_store()


__all__ = ["module_llm_model_registry_boot"]
