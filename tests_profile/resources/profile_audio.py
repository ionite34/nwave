import io
import logging
import os
import asyncio
import aiofiles
from numba import jit, njit
import ffmpeg
import soxr
import numpy as np
import soundfile as sf
import librosa
from nwave import Task, Config
from line_profiler_pycharm import profile


@profile
def process_file(task: Task) -> (int, Task):
    """
    Processes a single file
    """
    cfg = task.config
    try:
        data, sr = librosa.load(task.file_source, sr=None)
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
        start, end = cfg.silence_padding
        data = jit_pad(data, sr, start, end)

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


@profile
async def async_process_file(task: Task) -> (int, Task):
    """
    Processes a single file
    """
    cfg: Config = task.config
    try:
        data, sr = librosa.load(task.file_source, sr=None)
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

    # First save to memory using sf
    bytes_wav = bytes()
    bytes_io = io.BytesIO(bytes_wav)
    sf.write(bytes_io, data, sr, subtype=cfg.format, format='WAV')
    # Create task to save to file without waiting
    asyncio.create_task(async_save(bytes_wav, task.file_output))

    return 0, task


@profile
async def async_save(audio: bytes, file: str) -> None:
    """
    Saves audio to file asynchronously
    :param audio:
    :param file:
    :return:
    """
    async with aiofiles.open(file, 'wb') as f:
        await f.write(audio)


def jit_pad(data: np.ndarray, sr: int, pad_s: int, pad_e: int) -> np.ndarray:
    """
    Pads a wave array with zeros
    """
    # Convert from ms to seconds
    pad_s = pad_s / 1000
    pad_e = pad_e / 1000
    # Generate arrays using sample rate
    pad_start_samples = np.zeros(int(pad_s * sr))
    pad_end_samples = np.zeros(int(pad_e * sr))
    # Concatenate arrays and return
    return np.concatenate((pad_start_samples, data, pad_end_samples))


@profile
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
    out, err = None, None
    try:
        out, err = ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
    except ffmpeg.Error as e:
        logging.error(f"Error running ffmpeg: {err}")
        return 1, task
    return 0, task
