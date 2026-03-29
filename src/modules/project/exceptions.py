"""Project manager domain errors.

Exception messages are English only (logs, tracebacks). The GUI maps exception types
to localized strings via ``locmsg``; do not show ``str(exc)`` to end users for these types.
"""

from __future__ import annotations


class ProjectManagerError(Exception):
    """Base class for expected project manager failures."""


class ProjectNameEmptyError(ProjectManagerError):
    def __init__(self, message: str = "Project name cannot be empty.") -> None:
        super().__init__(message)


class ProjectAlreadyExistsError(ProjectManagerError):
    def __init__(self, message: str = "A project with this name already exists.") -> None:
        super().__init__(message)


class ProjectDeletePathOutsideError(ProjectManagerError):
    def __init__(
        self,
        message: str = "Deletion is only allowed for paths inside the projects directory.",
    ) -> None:
        super().__init__(message)


class ProjectFolderNotFoundError(ProjectManagerError):
    def __init__(self, message: str = "Project folder not found.") -> None:
        super().__init__(message)
