# Audio Processing Batch
from glob import glob

from .base import BaseEffect
from .core import WaveCore
from .scheduler import Task


class Batch:
    """
    A batch of audio files to process.
    """
    def __init__(self, input_files: list[str], output_files: list[str] = None,
                 in_place: bool = False, overwrite: bool = False):
        """
        Initialize a new batch.

        Args:
            input_files: List of source files to process.
            output_files: List of target files to write.
            in_place: Whether to overwrite the source files, target_files must be None if this is True.
            overwrite: Whether to overwrite the target files.
        """
        if in_place and not overwrite:
            raise ValueError("In-place processing requires overwrite to be True.")
        if in_place and output_files is not None:
            raise ValueError("In-place processing requires target_files to be None.")

        self.source_files = input_files
        self.output_files = output_files
        self.overwrite = overwrite
        self.in_place = in_place
        self.effects: list[BaseEffect] = []

    def run(self):
        """
        Run the batch.
        """
        with WaveCore() as core:
            tasks = self.export()
            core.schedule(tasks)
            return core.wait_all()

    def run_yield(self):
        """
        Run the batch and yield results.
        """
        with WaveCore() as core:
            tasks = self.export()
            core.schedule(tasks)
            return core.yield_all()

    def apply(self, *effects: BaseEffect):
        """
        Add effects to the batch.
        """
        self.effects.extend(effects)
        return self

    def export(self, target_files: list[str] = None, in_place: bool = False):
        """
        Export the batch to a new list of target files.

        Args:
            target_files: List of target files to write.
            in_place:
        Returns:
            StagedBatch: A batch of tasks objects.
        """
        if in_place and target_files:
            raise ValueError("In-place processing requires target_files to be None.")
        if target_files and len(target_files) != len(self.source_files):
            raise ValueError("Number of target files did not match number of source files.")

        if in_place:
            target_files = self.source_files
        elif target_files is None:
            target_files = self.output_files

        # Loop and yield tasks
        for source, target in zip(self.source_files, target_files):
            yield Task(source, target, self.effects, self.overwrite)

    @classmethod
    def from_glob(cls, pattern: str):
        """
        Create a new batch from a glob pattern.
        """
        # Search for files
        files = glob(pattern)
        if not files:
            raise ValueError(f"No files found for pattern {pattern}")
        return cls(files)
