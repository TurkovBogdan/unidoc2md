"""Protocol for optional API debug logging (raw response body)."""

from __future__ import annotations

from typing import Any, Protocol


class ResponseLoggerProtocol(Protocol):
    """
    Optional logger for raw API responses.

    May be omitted (None). Contract: ``debug()``, same shape as a typical extension logger.
    """

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...


__all__ = ["ResponseLoggerProtocol"]
