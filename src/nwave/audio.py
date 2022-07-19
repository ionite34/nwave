from __future__ import annotations

from scipy.io import wavfile

from nwave import interlocked
from nwave.task import Task
from nwave.task import TaskException


def process(task: Task):
    """
    Processes a single file
    """
    # Load
    try:
        sample_rate, data = wavfile.read(task.file_source)
    except Exception as ex:
        raise TaskException(ex, "File Loading") from ex

    # Run all effects
    for effect in task.effects:
        data, sample_rate = effect.apply_trace(data, sample_rate)

    # Normal write
    try:
        with interlocked.Writer(task.file_output, overwrite=task.overwrite) as file:
            wavfile.write(file, sample_rate, data)
    except Exception as ex:
        raise TaskException(ex, "File Writing") from ex
