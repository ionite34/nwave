import pytest
import typing
from nwave import effects, Batch, Task, TaskResult, TaskException


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


def test_batch_exceptions():
    # Test init value checks
    with pytest.raises(ValueError):  # in_place when overwrite is False
        Batch(['file1.wav'], ['file1_out.wav'], in_place=True)
    with pytest.raises(ValueError):  # in_place when target_files is not None
        Batch(['file1.wav'], ['file1.wav'], in_place=True, overwrite=True)


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
