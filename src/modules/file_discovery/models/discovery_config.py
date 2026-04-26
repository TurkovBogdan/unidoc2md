"""Discovery config: path, extensions, hash, recursion."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiscoveryConfig:
    """Parameters for directory traversal and file filtering."""

    path: str
    # By default match all files; supported extensions may be provided from outside
    # (e.g. from FileExtractService).
    extensions: set[str] = field(default_factory=lambda: {"*"})
    hash: bool = True
    recursive_search: bool = True
