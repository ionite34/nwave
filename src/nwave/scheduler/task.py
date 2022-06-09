from collections import namedtuple
from dataclasses import dataclass

from .config import FrozenConfig


@dataclass(frozen=True)
class Task:
    """
    Holds information for an audio processing task
    """
    file_source: str
    file_output: str
    config: FrozenConfig
    overwrite: bool = False


# Define a named tuple for task result
TaskResult = namedtuple('TaskResult', ['task', 'success', 'error'])
