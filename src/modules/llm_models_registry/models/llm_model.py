"""Domain model for an LLM-provider model: capabilities and API metadata."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class LLMModel:
    """
    Provider-facing model: identity, input/output modalities,
    feature flags and context. Used when listing models from an API before persisting to the registry.
    """

    # Identity
    provider: str
    name: str

    # Registry merge policy
    can_update: bool = False  # service flag for merge/boot; set False after user edits
    enabled: bool = True

    # Input modalities
    input_text: bool = False
    input_image: bool = False
    input_audio: bool = False
    input_video: bool = False

    # Output modalities
    output_text: bool = False
    output_image: bool = False
    output_audio: bool = False
    output_video: bool = False

    # Features
    chat: bool = False
    function_calling: bool = False
    structured_output: bool = False
    reasoning: bool = False

    # Context / pricing
    context_window: int | None = None
    price_input: float | None = None
    price_output: float | None = None

    # Metadata (timestamp)
    created: int = 0

    def to_registry_record(self) -> dict[str, Any]:
        """Serialize to a registry record dict (for ``store.data``)."""
        return asdict(self)
