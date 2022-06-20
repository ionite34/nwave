# Audio loading and transformation / converts
from __future__ import annotations

import os
import logging
import librosa
import numpy as np
import soundfile as sf
import soxr
from scipy.io import wavfile

from .exceptions import TaskException
from .scheduler import Task
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


def process_old(task: Task) -> (int, Task):
    """
    Processes a single file
    """
    cfg = task.config

    # Load
    data, sr = librosa.load(task.file_source, sr=None)

    # Resampling
    if cfg.sample_rate and cfg.sample_rate != sr:
        data = soxr.resample(data, sr, cfg.sample_rate, quality=cfg.resample_quality)
        sr = cfg.sample_rate

    # Silence Padding
    if cfg.silence_padding:
        start, end = cfg.silence_padding
        data = pad(data, sr, start, end)

    # Skip if exists and no overwrite option
    if not task.overwrite and os.path.exists(task.file_output):
        logging.info(f"File {task.file_output} already exists, skipping")
        return 0, task

    # Normal write
    with interlocked.Writer(task.file_output) as f:
        wavfile.write(f, sr, data)
    return 0, task


def pad(data: np.ndarray, sr: int, pad_s: int, pad_e: int) -> np.ndarray:
    """
    Pads a wave array with silence
    """
    if pad_s < 0 or pad_e < 0:
        raise ValueError(f"Padding of ({pad_s}, {pad_e}) must be positive")
    # Convert from ms to samples
    pad_s = int(pad_s / 1000 * sr)
    pad_e = int(pad_e / 1000 * sr)
    # Generate arrays using sample rate
    pad_start_samples = np.zeros(pad_s, dtype=np.float32)
    if pad_e == pad_s:
        pad_end_samples = pad_start_samples
    else:
        pad_end_samples = np.zeros(pad_e, dtype=np.float32)
    # Concatenate arrays and return
    return np.concatenate((pad_start_samples, data, pad_end_samples), dtype=np.float32)
