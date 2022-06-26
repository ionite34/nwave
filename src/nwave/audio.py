from __future__ import annotations

from scipy.io import wavfile

from .scheduler import Task, TaskException
from . import interlocked


def process(task: Task):
    """
    Processes a single file
    """
    # Load
    try:
        # data, sr = librosa.load(task.file_source, sr=None)
        sr, data = wavfile.read(task.file_source)
    except Exception as e:
        raise TaskException(e, 'File Loading')

    # Run all effects
    for effect in task.effects:
        data, sr = effect.apply_trace(data, sr)

    # Normal write
    try:
        with interlocked.Writer(task.file_output, overwrite=task.overwrite) as f:
            wavfile.write(f, sr, data)
    except Exception as e:
        raise TaskException(e, 'File Writing')
