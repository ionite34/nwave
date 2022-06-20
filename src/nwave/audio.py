# Audio loading and transformation / converts
from __future__ import annotations

import os
import logging
import librosa
import numpy as np
import soundfile as sf
import soxr
from scipy.io import wavfile

from .scheduler import Task, TaskException
from . import interlocked


# Set of extensions compatible with SoundFile


def process(task: Task):
    """
    Processes a single file
    """
    # Load
    try:
        data, sr = librosa.load(task.file_source, sr=None)
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
