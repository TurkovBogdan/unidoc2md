"""Runtime extract configuration: built from project-level extract payload, used only while extracting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.utils.hash import md5_string


@dataclass
class ExtractConfig:
    """Extract configuration for a single run. Built from group-based extract payload. Not the project-level schema/payload API."""

    project_path: Path | str
    """provider -> { schema field key -> value }. Filled from normalized payload via the schema registry."""
    provider_configs: dict[str, dict[str, Any]] | None = None
    cache_path: Path | None = None

    def __post_init__(self) -> None:
        if self.provider_configs is None:
            object.__setattr__(self, "provider_configs", {})

    def get_provider_value(self, provider_code: str, key: str, default: Any = None) -> Any:
        """Provider field value by schema key."""
        cfg = (self.provider_configs or {}).get(provider_code) or {}
        return cfg.get(key, default)

    @property
    def cache_dir(self) -> Path:
        """Extract cache directory: cache_path if set, else <project>/extract/."""
        if self.cache_path is not None:
            return self.cache_path
        base = Path(self.project_path) if isinstance(self.project_path, str) else self.project_path
        return base / "extract"

    def to_canonical_string(self) -> str:
        """Canonical string of all parameters (no filesystem paths) for hashing. Combined with file hash for cache key."""
        parts: list[str] = []
        pc = self.provider_configs or {}
        for code in sorted(pc):
            vals = pc[code]
            for k in sorted(vals):
                parts.append(f"providers.{code}.{k}={vals[k]!r}")
        return "\n".join(parts)

    def canonical_hash(self) -> str:
        """Hash of the canonical config string (no paths)."""
        return md5_string(self.to_canonical_string())
