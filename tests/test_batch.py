import pytest
import typing
from nwave import Batch, Task, TaskResult, effects
from nwave.exceptions import TaskException


def test_batch():
    # Create a batch
    batch = Batch(['file1.wav'], ['file1_out.wav'])
    assert batch.source_files == ['file1.wav']
    assert batch.output_files == ['file1_out.wav']
    assert batch.in_place is False
    assert batch.overwrite is False
    # Add Effects
    batch.apply(
        effects.Resample(44100),
        effects.PadSilence(0.5, 0.5)
    )
    # Export
    assert isinstance(batch, Batch)
    staged = batch.export()
    assert isinstance(staged, typing.Generator)
    # Unpack Generator
    for task in staged:
        assert isinstance(task, Task)
        # Check effects
        assert len(task.effects) == 2
        assert isinstance(task.effects[0], effects.Resample)
        assert isinstance(task.effects[1], effects.PadSilence)


def test_run():
    # Create a batch
    batch = Batch(['file1.wav'], ['file1_out.wav'])
    # Add Effects
    batch.apply(
        effects.Resample(44100),
        effects.PadSilence(0.5, 0.5)
    )
    # Run
    results = batch.run()
    for result in results:
        assert isinstance(result, TaskResult)
        assert result.success is False
        assert isinstance(result.error, TaskException)
