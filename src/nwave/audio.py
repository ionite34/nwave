# Audio loading and transformation / converts
from __future__ import annotations

import os
import logging
import librosa
import numpy as np
import soundfile as sf
import ffmpeg

import dask.array as da

import soxr
from os import PathLike
from .engine import Task


def load(file: str | bytes | PathLike, resample_to: int = None) -> (np.ndarray, int):
    """
    Loads a sound file using librosa
    """
    data, samplerate = librosa.load(file, sr=resample_to)
    return data, samplerate


def save(file: str | bytes | PathLike, data: np.ndarray, samplerate: int) -> None:
    """
    Saves a sound file using soundfile
    """
    sf.write(file, data, samplerate)


def combined(in_file, out_file, resample_to=None):
    data, samplerate = librosa.load(in_file, sr=resample_to, res_type='kaiser_fast')
    save(out_file, data, samplerate)


def process_file(task: Task) -> (int, Task):
    """
    Processes a single file
    """
    cfg = task.config
    try:
        data, sr = load(task.file_source, resample_to=None)
    except IOError:
        logging.error(f"Error loading file {task.file_source}")
        return 1, task

    if cfg.sample_rate and cfg.sample_rate != sr:
        try:
            data = soxr.resample(data, sr, cfg.sample_rate, quality=cfg.resample_quality)
            sr = cfg.sample_rate
        except ValueError:
            logging.error(f"Error resampling file {task.file_source}")
            return 1, task

    if cfg.silence_padding:
        try:
            s = cfg.silence_padding[0] / 1000
            e = cfg.silence_padding[1] / 1000
            pad_start_samples = np.zeros(int(s * sr))
            pad_end_samples = np.zeros(int(e * sr))
            data = np.concatenate((pad_start_samples, data, pad_end_samples))
        except ValueError:
            logging.error(f"Error padding file {task.file_source}")

    # Skip if exists and no overwrite option
    if not task.overwrite and os.path.exists(task.file_output):
        logging.info(f"File {task.file_output} already exists, skipping")
        return 0, task

    try:
        sf.write(task.file_output, data, sr, subtype=cfg.format)
    except IOError:
        logging.error(f"Error saving file {task.file_output}")
        return 1, task

    return 0, task


def process_ffmpeg(task: Task) -> (int, Task):
    stream = ffmpeg.input(task.file_source)
    # Add silence padding to beginning
    pad_s = task.config.silence_padding[0]
    stream = ffmpeg.filter(stream, "adelay", pad_s)
    # Add silence padding to end
    pad_e = task.config.silence_padding[1]
    stream = ffmpeg.filter(stream, "apad", f"pad_dur={pad_e}")
    # Output as resampled
    stream = ffmpeg.output(stream, task.file_output, ac=1, ar=task.config.sample_rate)
    try:
        out, err = ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
    except ffmpeg.Error as e:
        logging.error(f"Error running ffmpeg: {e}")
        return 1, task
    return 0, task
