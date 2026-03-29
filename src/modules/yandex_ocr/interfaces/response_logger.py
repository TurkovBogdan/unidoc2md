"""Protocol for optional API debug logging (raw response body)."""

from __future__ import annotations

from typing import Any, Protocol


class ResponseLoggerProtocol(Protocol):
    """
    Optional logger for raw API responses.

    May be omitted (None) and is then unused. Contract is ``debug()``,
    same as IExtensionLogger (extension.logger.logger_protocol).
    """

    def debug(self, msg: Any, *args: Any, **kwargs: Any) -> None: ...


__all__ = ["ResponseLoggerProtocol"]
