# Audio Processing Batch
from typing import Iterable
from glob import glob
from typing import Generator
from .scheduler import Task, Config


class Batch:
    """
    A batch of audio files to process.
    """

    def __init__(self, source_files: list[str], target_files: list[str] = None,
                 in_place: bool = False, overwrite: bool = False):
        """
        Initialize a new batch.

        Args:
            source_files: List of source files to process.
            in_place: Whether to overwrite the source files, target_files must be None if this is True.
            overwrite: Whether to overwrite the target files.
        """
        if in_place and not overwrite:
            raise ValueError("In-place processing requires overwrite to be True.")
        if in_place and target_files is not None:
            raise ValueError("In-place processing requires target_files to be None.")

        self.source_files = source_files
        self.overwrite = overwrite
        self.in_place = in_place
        self.config = Config()
        self.tasks = []

    def resample(self, sample_rate: int):
        """
        Resample the batch.

        Args:
            sample_rate: Target Sample Rate in Hz.
        """
        self.config.sample_rate = sample_rate
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

        # Loop and yield tasks
        for source, target in zip(self.source_files, target_files):
            yield Task(source, target, self.config.frozen(), self.overwrite)

    @classmethod
    def fromGlob(cls, pattern: str):
        """
        Create a new batch from a glob pattern.
        """
        # Search for files
        files = glob(pattern)
        if not files:
            raise ValueError(f"No files found for pattern {pattern}")
        return cls(files)
