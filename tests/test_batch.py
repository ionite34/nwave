from __future__ import annotations

import os
from glob import glob

from nwave import Batch
from nwave import effects
from nwave import Task
from nwave import TaskException
from nwave import TaskResult


def test_batch():
    # Create using string, not list
    batch = Batch("file1.wav", "file1_out.wav")
    assert batch.overwrite is False
    # Add Effects
    batch.apply(effects.Resample(44100), effects.PadSilence(0.5, 0.5))
    # Unpack
    for task in batch.tasks:
        assert isinstance(task, Task)
        # Check effects
        assert len(task.effects) == 2
        assert isinstance(task.effects[0], effects.Resample)
        assert isinstance(task.effects[1], effects.PadSilence)


def test_batch_run_yield(data_dir):
    # Get wav files in data_dir
    src_files = glob(os.path.join(data_dir, "*.wav"))
    out_files = [f.replace(".wav", "_out.wav") for f in src_files]
    # Create a task batch
    batch = Batch(src_files, out_files)
    batch.apply(
        effects.Resample(44100),
    )
    results = batch.run_yield()
    for result in results:
        assert isinstance(result, TaskResult)
        assert result.success


def test_run():
    # Create a batch
    batch = Batch(["file1.wav"], ["file1_out.wav"])
    # Add Effects
    batch.apply(effects.Resample(44100), effects.PadSilence(0.5, 0.5))
    # Run
    results = batch.run()
    for result in results:
        assert isinstance(result, TaskResult)
        assert result.success is False
        assert isinstance(result.error, TaskException)
