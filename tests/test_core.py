import os
from glob import glob
from unittest.mock import patch

import pytest

from nwave import WaveCore, Batch, effects
from nwave import __version__


def test_version():
    assert __version__ == "0.1.0"


def test_core(data_dir):
    # Get wav files in data_dir
    src_files = glob(os.path.join(data_dir, "*.wav"))
    out_files = [f.replace(".wav", "_out.wav") for f in src_files]
    # Test context manager
    with WaveCore() as core:
        # Create a task batch
        batch = Batch(src_files, out_files)
        batch.apply(
            effects.Resample(44100),
        )
        core.schedule(batch)
        assert core.n_tasks == len(src_files)
        # Wait for all tasks to complete
        for result in core.yield_all(timeout=10):
            assert result.success
            assert result.error is None


def test_core_enter():
    with WaveCore() as core:
        assert isinstance(core, WaveCore)


def test_core_yield_all(data_dir):
    # Test that yield_all cancels if we don't iterate over all results
    with WaveCore() as core:
        src_files = glob(os.path.join(data_dir, "*.wav"))
        out_files = [f.replace(".wav", "_out.wav") for f in src_files]
        # Create a task batch
        batch = Batch(src_files, out_files)
        batch.apply(
            effects.Resample(44100),
        )
        # Schedule batch
        core.schedule(batch)
        # Get generator
        results = core.yield_all(timeout=30)
        # Get first result
        next(results)
        # Now patch the `time.monotonic` function to raise an exception
        with patch("time.monotonic", side_effect=RuntimeError):
            # Try to get the next results
            with pytest.raises(RuntimeError):
                next(results)


def test_core_glob(data_dir):
    # Test glob mode
    with WaveCore() as core:
        batch = Batch.from_glob(
            os.path.join(data_dir, "*.wav"), data_dir, overwrite=True
        )
        core.schedule(batch)

        for result in core.yield_all():
            assert result.success


def test_core_glob_ex():
    # Test no files found
    with pytest.raises(ValueError):
        Batch.from_glob("no_exists/*.wav", "no_exists/")
