from __future__ import annotations

from pprint import pformat
import inspect
from concurrent.futures import CancelledError
from dataclasses import dataclass
from ..base import BaseEffect


@dataclass(frozen=True)
class Task:
    """
    Holds information for an audio processing task
    """
    file_source: str
    file_output: str
    # config: FrozenConfig
    effects: list[BaseEffect]
    overwrite: bool = False


@dataclass(frozen=True)
class TaskResult:
    task: Task
    success: bool
    error: Exception | None = None

    def __str__(self):
        if self.success:
            status = 'Completed'
        elif isinstance(self.error, CancelledError):
            status = 'Cancelled'
        else:
            status = 'Failed'

        if status == 'Failed':
            return (f"Task: {self.task.file_source} -> {self.task.file_output}\n"
                    f"[{status}]: {self.error}")
        else:
            return (f"Task: {self.task.file_source} -> {self.task.file_output}\n"
                    f"[{status}]")


class TaskException(Exception):
    def __init__(self, exception, during: str = None):
        """
        Exceptions raised during task run.

        Args:
            exception: The exception that was raised.
            during: The name of the function that raised the exception.
        """
        self.inner_exception = exception
        self.inner_type = exception.__class__.__name__
        self.raising_source = during

    def __str__(self):
        if self.raising_source:
            return f"During {self.raising_source} -> {self.inner_type}: {self.inner_exception}"
        else:
            return str(self.inner_exception)
