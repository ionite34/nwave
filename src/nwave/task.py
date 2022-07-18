from __future__ import annotations

import typing as t
from concurrent.futures import CancelledError
from dataclasses import dataclass
from os import PathLike
from pathlib import Path

if t.TYPE_CHECKING:  # pragma: no cover
    from nwave.base import BaseEffect

# Make a type alias for AnyPath
AnyPath = t.Union[str, PathLike, Path]


@dataclass(init=False)
class Task:
    """Defines an audio processing task."""

    file_source: Path
    file_output: Path
    effects: list[BaseEffect]
    overwrite: bool

    def __init__(
        self,
        file_source: AnyPath,
        file_output: AnyPath,
        effects: list[BaseEffect],
        overwrite: bool,
    ):
        self.file_source = (
            file_source if isinstance(file_source, Path) else Path(file_source)
        )
        self.file_output = (
            file_output if isinstance(file_output, Path) else Path(file_output)
        )
        self.effects = effects
        self.overwrite = overwrite


@dataclass(frozen=True)
class TaskResult:
    """Result of a task."""

    task: Task
    error: BaseException | None = None

    @property
    def success(self) -> bool:
        """Whether the task was successful."""
        return not self.error

    def __str__(self):
        if self.success:
            status = "[Completed]"
        elif isinstance(self.error, CancelledError):
            status = "[Cancelled]"
        else:
            status = f"[Failed]: {self.error}"

        return f"Task: {self.task.file_source} -> {self.task.file_output}\n{status}"


class TaskException(Exception):
    """Exception raised when a task fails."""

    def __init__(self, exception, during: str = None):
        """
        Exceptions raised during task run.

        Args:
            exception: The exception that was raised.
            during: The name of the function that raised the exception.
        """
        super().__init__(exception)
        self.inner_exception = exception
        self.inner_type = exception.__class__.__name__
        self.raising_source = during

    def __str__(self):
        if self.raising_source:
            return (
                f"During {self.raising_source} -> "
                f"{self.inner_type}: {self.inner_exception}"
            )
        return str(self.inner_exception)
