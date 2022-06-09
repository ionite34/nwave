import pytest
import typing
from nwave import Batch, Task


def test_batch():
    # Create a batch
    batch = Batch(['/path/to/file1.wav'])
    assert batch.source_files == ['/path/to/file1.wav']
    assert batch.in_place is False
    assert batch.overwrite is False
    # Add Effects
    assert batch.config.sample_rate is None
    batch.resample(44100)
    assert batch.config.sample_rate == 44100
    # Export
    assert isinstance(batch, Batch)
    staged = batch.export(['/path/to/file1_resampled.wav'])
    assert isinstance(staged, typing.Generator)
    # Unpack Generator
    for task in staged:
        print(task)
        assert isinstance(task, Task)
