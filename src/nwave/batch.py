from __future__ import annotations

import os
from glob import glob
from typing import Iterable, Iterator

from .base import BaseEffect
from .core import WaveCore
from .task import Task, TaskResult


class Batch:
    def __init__(
        self,
        input_files: Iterable[str | os.PathLike],
        output_files: Iterable[str | os.PathLike],
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
        self.tasks = [
            Task(src, dst, self.effects, self.overwrite)
            for src, dst in zip(input_files, output_files)
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
