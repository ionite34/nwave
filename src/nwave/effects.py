from __future__ import annotations

import numbers
from typing import Callable, SupportsFloat

import librosa
import numpy as np
import soxr
from numpy.typing import NDArray
from typing_extensions import Literal

from nwave.abc import BaseEffect

__all__ = ["Wrapper", "Resample", "PadSilence", "TimeStretch", "PitchShift"]

Quality = Literal["QQ", "LQ", "MQ", "HQ", "VHQ"]
QUALITIES = {"QQ", "LQ", "MQ", "HQ", "VHQ"}


class Wrapper(BaseEffect):
    def __init__(
        self,
        function: Callable,
        data_arg: str | None = None,
        sr_arg: str | None = None,
        output_sr: float | None = None,
        **kwargs,
    ) -> None:
        """
        Wrapper for any Callable as an Audio Effect. The function
        must return a NDArray or a 2 length tuple containing a NDArray
        and a float or int as the sample rate, in either order.

        Args:
            callable: Callable to wrap
            data_arg: Name of the data keyword argument of type NDArray. If
                None, the first positional argument will be used.
            sr_arg: Name of the sample rate keyword argument of type float
            output_sr: Define a fixed output expected sample rate
                for cases where only one element of NDArray is returned. If not
                specified, the output sample rate will be the same as the input.
            kwargs: Additional keyword arguments to pass to the callable
        """
        super().__init__()
        # Check if callable
        if not callable(function):
            raise TypeError(f"Expected Callable, got {type(function)}")
        self._function = function
        self._kwargs = kwargs  # Store kwargs to pass to function
        self._data_arg = data_arg
        self._sr_arg = sr_arg
        self._output_sr = output_sr

    def apply(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        # Add the data and sr keyword arguments
        if self._sr_arg:
            self._kwargs[self._sr_arg] = sr
        if self._data_arg:
            self._kwargs[self._data_arg] = data
            result = self._function(**self._kwargs)
        else:
            # If no data kwarg supplied, add the first positional argument as data
            result = self._function(data, **self._kwargs)

        # For NDArray, return the original sr with it
        if isinstance(result, np.ndarray):
            # If override is defined, return the override
            if self._output_sr is not None:
                return result, self._output_sr
            return result, sr
        # For 2 length tuple, return the correct ordered result
        elif isinstance(result, tuple) and len(result) == 2:
            if isinstance(result[0], np.ndarray) and isinstance(
                result[1], (int, float)
            ):
                return result[0], float(result[1])
            if isinstance(result[1], np.ndarray) and isinstance(
                result[0], (int, float)
            ):
                return result[1], float(result[0])
        # Otherwise raise an error
        raise TypeError(
            "Function expected to return NDArray "
            f"or tuple containing NDArray and float, got {type(result).__name__} "
            f"of {repr(result)}"
        )


class Resample(BaseEffect):
    def __init__(self, sample_rate: SupportsFloat, quality: Quality = "HQ") -> None:
        """
        Resamples the audio to a new sample rate.

        Args:
            sample_rate: Target Sample Rate in Hz.
            quality: Resample Quality (One of 'QQ', 'LQ', 'MQ', 'HQ', 'VHQ')
        """
        super().__init__()
        self.sample_rate = float(sample_rate)
        self.quality = quality
        if not self.sample_rate > 0:
            raise ValueError("Sample rate should be above 0.")
        if self.quality not in QUALITIES:
            raise ValueError(
                f"Invalid quality: {self.quality}. Must be one of {QUALITIES}"
            )

    def apply(self, data, sr) -> tuple[NDArray, float]:
        if sr == self.sample_rate:
            return data, sr  # Skip processing if already at target sample rate
        return (
            soxr.resample(
                data, in_rate=sr, out_rate=self.sample_rate, quality=self.quality
            ),
            self.sample_rate,
        )


class PadSilence(BaseEffect):
    def __init__(self, start: float, end: float) -> None:
        """
        Pads the beginning and end of the audio with silence.

        Args:
            start: Padding to add to the start of the audio in seconds.
            end: Padding to add to the end of the audio in seconds.
        """
        if start < 0 or end < 0:
            raise ValueError("Padding must be positive.")
        super().__init__()
        self.start = start
        self.end = end

    def apply(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        """
        Pads a wave array with silence

        Args:
            data: Wave array to pad
            sr: Sample rate of the wave array

        Returns:
            Tuple of (padded wave array, sample rate)
        """
        # Convert from seconds to samples
        pad_s = int(self.start * sr)
        pad_e = int(self.end * sr)
        # Generate zero arrays
        start_samples = np.zeros(pad_s, dtype=np.float32)
        end_samples = np.zeros(pad_e, dtype=np.float32)
        # Concatenate arrays and return
        return np.concatenate((start_samples, data, end_samples), dtype=np.float32), sr


class TimeStretch(BaseEffect):
    def __init__(self, factor: float) -> None:
        """
        Time stretches the audio by a factor.

        Args:
            factor: Time stretch factor. >1.0 will speed up, <1.0 will slow down.
        """
        if factor <= 0:
            raise ValueError("Factor must be positive.")
        super().__init__()
        self.factor = factor

    def apply(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        """
        Time stretches a wave array by a factor.
        """
        return librosa.effects.time_stretch(data, rate=self.factor), sr


class PitchShift(BaseEffect):
    def __init__(
        self,
        sample_rate: float,
        n_steps: float,
        bins_per_octave: float = 12,
        quality: Quality = "HQ",
    ) -> None:
        """
        Pitch shifts the audio by ``n_steps``. This will also resample the audio.

        A step is equal to a semitone if ``bins_per_octave`` is set to 12.

        Uses ``librosa.effects.pitch_shift``

        Args:
            n_steps: Number of steps to shift the audio. >0 will shift up,
                <0 will shift down.
            bins_per_octave: Number of steps per octave.
            sample_rate: Sampling rate for the output audio.
            quality: Resample Quality (One of 'QQ', 'LQ', 'MQ', 'HQ', 'VHQ')
        """
        super().__init__()
        if not isinstance(sample_rate, numbers.Real) or sample_rate <= 0:
            raise ValueError("Sample rate must be a positive real number.")
        if quality not in QUALITIES:
            raise ValueError(f"Invalid quality: {quality}. Must be one of {QUALITIES}")
        self.sample_rate: float = sample_rate
        self.n_steps: float = n_steps
        self.bins_per_octave: float = bins_per_octave
        self.quality: Quality = quality

    def apply(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        """
        Pitch shifts a wave array.
        """
        return (
            librosa.effects.pitch_shift(
                y=data,
                sr=self.sample_rate,
                n_steps=self.n_steps,
                bins_per_octave=self.bins_per_octave,
                res_type=f"soxr_{self.quality.lower()}",
            ),
            self.sample_rate,
        )
