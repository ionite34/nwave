# Exceptions

# Task Exception
from __future__ import annotations

from types import TracebackType


class TaskException(Exception):
    """
    Base Task Exception
    """

    def __init__(self, exception: Exception, raised_by: str, tb: TracebackType | None = None):
        super().__init__(exception)
        self.__traceback__ = tb
        self.raised_by = raised_by
