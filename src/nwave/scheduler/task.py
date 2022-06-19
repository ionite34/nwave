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
    error: Exception = None

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

        # Determine the name of the function that raised the exception.
        # Careful not to leave references after init
        stack = inspect.stack()
        raising_instance = stack[1].frame.f_locals.get('self', None)
        # Name of the raising class
        self.raising_class = raising_instance.__class__.__name__ if raising_instance else None
        # Name of the raising function
        raising_method = stack[1].frame.f_code.co_name
        # Raising variables in scope
        self.cls_vars = stack[1].frame.f_code.co_varnames
        self.raising_method = raising_method if raising_method else None

        # If raised by a valid class, pretty format the instance variables.
        # if raising_instance:
        # self.cls_vars = vars(raising_instance)

    def __str__(self):
        if self.raising_class:
            msg = f"({self.inner_type}) {self.inner_exception} raised during {self.raising_class}.{self.raising_method}"
            msg += f"\n{pformat(self.cls_vars)}"
            return msg
        else:
            return str(self.inner_exception)
