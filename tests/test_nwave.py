import os
from glob import glob

from nwave import __version__
from nwave import WaveCore, Batch, effects


def test_version():
    assert __version__ == '0.1.0'


def test_wave_core(data_dir):
    # Get wav files in data_dir
    src_files = glob(os.path.join(data_dir, "*.wav"))
    out_files = [f.replace(".wav", "_out.wav") for f in src_files]
    # Test context manager
    with WaveCore() as core:
        # Create a task batch
        batch = Batch(src_files)
        batch.apply(
            effects.Resample(44100),
        )
        staged = batch.export(out_files)
        # Add to scheduler
        core.schedule(staged)
        # Wait for all tasks to complete
        for result in core.yield_all():
            assert result.success
            assert result.error is None
