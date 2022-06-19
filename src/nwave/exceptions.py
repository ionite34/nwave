from __future__ import annotations


class TaskException(Exception):
    def __init__(self, exception: Exception, raised_by: str):
        """ Initialize a new TaskException. """
        super().__init__(exception)
        self.raised_by = raised_by

    def __str__(self):
        return f"During [{self.raised_by}] -> {self.args[0]}"
