from __future__ import annotations

import os
from glob import glob
from os import PathLike
from pathlib import Path
from typing import Iterable
from typing import Iterator
from typing import NamedTuple

from .base import BaseEffect
from .core import WaveCore
from .task import Task
from .task import TaskResult


class Paths(NamedTuple):
    """Paths for file processing pair."""

    source: Path
    target: Path


def parse_path(
    input_files: Iterable[str | PathLike] | str | PathLike,
    output_files: Iterable[str | PathLike] | str | PathLike,
) -> list[Paths]:
    """
    Parses input and output files.
    If str, assumes directory.
    If iterable, use files within.

    Args:
        input_files: Input files.
        output_files: Output files.

    Returns:
        List of namedtuple Paths[source, target]
    """
    result: list[Paths] = []
    # If inputs are str, wrap in list
    if isinstance(input_files, (str, PathLike)):
        input_files = [input_files]
    if isinstance(output_files, (str, PathLike)):
        output_files = [output_files]

    # Convert to Path
    result = [
        Paths(Path(src), Path(dst)) for src, dst in zip(input_files, output_files)
    ]
    return result


class Batch:
    def __init__(
        self,
        input_files: Iterable[str | PathLike] | str,
        output_files: Iterable[str | PathLike] | str,
        overwrite: bool = False,
    ):
        """
        Initialize a new batch.

        Args:
            input_files: List of source files to process.
            output_files: List of target files to write.
            overwrite: Whether to overwrite the target files.
        """
        self.overwrite = overwrite
        self.effects: list[BaseEffect] = []
        # Get list of Path tuples
        paths = parse_path(input_files, output_files)
        # Create tasks
        self.tasks = [
            Task(src, dst, self.effects, self.overwrite) for src, dst in paths
        ]

    def run(self, threads: int | None = None) -> list[TaskResult]:
        """
        Run the batch.

        Args:
            threads: Number of threads to use.

        Returns:
            A list of TaskResults.
        """
        with WaveCore(threads) as core:
            core.schedule(self)
            return core.wait_all()

    def run_yield(self, threads: int | None = None) -> Iterator[TaskResult]:
        """
        Run the batch and yield results.

        Args:
            threads: Number of threads to use.

        Returns:
            A generator of TaskResults.
        """
        with WaveCore(threads) as core:
            core.schedule(self)
            yield from core.yield_all()

    def apply(self, *effects: BaseEffect):
        """
        Add effects to the batch.
        """
        self.effects.extend(effects)
        return self

    @classmethod
    def from_glob(cls, pattern: str, dest_dir: str, overwrite: bool = False) -> Batch:
        """
        Create a new batch from a glob pattern.
        """
        # Search for files
        files = glob(pattern)
        if not files:
            raise ValueError(f"No files found for pattern {pattern}")
        return cls(
            files,
            [os.path.join(dest_dir, os.path.basename(f)) for f in files],
            overwrite,
        )
