# Audio Effects
from functools import lru_cache

import numpy as np

from ._base import BaseEffect
from numpy.typing import NDArray
import soxr


class Resample(BaseEffect):
    def __init__(self, sample_rate: int, quality: str = 'HQ'):
        """
        Resamples the audio to a new sample rate.

        Args:
            sample_rate: Target Sample Rate in Hz.
            quality: Resample Quality (One of 'QQ', 'LQ', 'MQ', 'HQ', 'VHQ')
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.quality = quality
        self.qualities = {'QQ', 'LQ', 'MQ', 'HQ', 'VHQ'}
        if self.quality not in self.qualities:
            raise ValueError(f'Invalid quality: {self.quality}. Must be one of {self.qualities}')

    def _apply(self, data, sr):
        if sr == self.sample_rate:
            return data, sr  # Skip if no change
        return soxr.resample(data, in_rate=sr, out_rate=self.sample_rate)


class PadSilence(BaseEffect):
    def __init__(self, start: float, end: float):
        """
        Pads the beginning and end of the audio with silence.

        Args:
            start: Padding to add to the start of the audio in seconds.
            end: Padding to add to the end of the audio in seconds.
        """
        if start < 0 or end < 0:
            raise ValueError('Padding must be positive.')
        super().__init__()
        self.start = start
        self.end = end

    def _apply(self, data, sr):
        """
        Pads a wave array with silence
        """
        # Convert from seconds to samples
        pad_s = int(self.start * sr)
        pad_e = int(self.end * sr)
        # Generate zero arrays
        start_samples = np.zeros(pad_s, dtype=np.float32)
        if pad_e == pad_s:
            pad_end_samples = pad_start_samples
        else:
            pad_end_samples = np.zeros(pad_e, dtype=np.float32)
        # Concatenate arrays and return
        return np.concatenate((pad_start_samples, data, pad_end_samples), dtype=np.float32)
