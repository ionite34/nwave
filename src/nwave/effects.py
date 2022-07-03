from __future__ import annotations

import numbers
from typing import Callable
from numpy.typing import NDArray
import numpy as np

from .base import BaseEffect

import soxr

__all__ = ["Wrapper", "Resample", "PadSilence"]


class Wrapper(BaseEffect):
    def __init__(
        self,
        function: Callable,
        data_arg: str | None = None,
        sr_arg: str | None = None,
        output_sr_override: float | None = None,
        **kwargs,
    ):
        """
        Wrapper for any Callable as an Audio Effect. The function
        must return a NDArray or a 2 length tuple containing a NDArray
        and a float or int as the sample rate.

        Args:
            callable: Callable to wrap
            data_arg: Name of the data keyword argument of type NDArray. If
                None, the first positional argument will be used.
            sr_arg: Name of the sample rate keyword argument of type float
            output_sr_override: Define a fixed output expected sample rate
                for cases where only one element of NDArray is returned
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
        self._output_sr_override = output_sr_override

    def apply(self, data: NDArray, sr: float) -> tuple[NDArray, float]:
        # Add the data and sr keyword arguments
        kwargs = self._kwargs
        if self._sr_arg:
            kwargs[self._sr_arg] = sr
        if self._data_arg:
            kwargs[self._data_arg] = data
            result = self._function(**kwargs)
        else:
            # If no data kwarg supplied, add the first positional argument as data
            result = self._function(data, **kwargs)

        # For NDArray, return the original sr with it
        if isinstance(result, np.ndarray):
            # If override is defined, return the override
            if self._output_sr_override is not None:
                return result, self._output_sr_override
            else:
                return result, sr
        # For 2 length tuple, return the correct ordered result
        elif isinstance(result, tuple) and len(result) == 2:
            if isinstance(result[0], np.ndarray) and isinstance(
                result[1], numbers.Real
            ):
                return result[0], result[1]
            elif isinstance(result[1], np.ndarray) and isinstance(
                result[0], numbers.Real
            ):
                return result[1], result[0]
        # Otherwise raise an error
        raise TypeError(
            "Function expected to return NDArray "
            f"or tuple containing [NDArray, float], got {type(result).__name__}"
        )


class Resample(BaseEffect):
    def __init__(self, sample_rate: int, quality: str = "HQ"):
        """
        Resamples the audio to a new sample rate.

        Args:
            sample_rate: Target Sample Rate in Hz.
            quality: Resample Quality (One of 'QQ', 'LQ', 'MQ', 'HQ', 'VHQ')
        """
        super().__init__()
        self.sample_rate = sample_rate
        self.quality = quality
        self.qualities = {"QQ", "LQ", "MQ", "HQ", "VHQ"}
        if not isinstance(self.sample_rate, numbers.Real) or self.sample_rate <= 0:
            raise ValueError("Sample rate must be a positive real number.")
        if self.quality not in self.qualities:
            raise ValueError(
                f"Invalid quality: {self.quality}. Must be one of {self.qualities}"
            )

    def apply(self, data, sr) -> tuple[NDArray, float]:
        if sr == self.sample_rate:
            return data, sr  # Skip processing if already at target sample rate
        return (
            soxr.resample(data, in_rate=sr, out_rate=self.sample_rate),
            self.sample_rate,
        )


class PadSilence(BaseEffect):
    def __init__(self, start: float, end: float):
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
        """
        # Convert from seconds to samples
        pad_s = int(self.start * sr)
        pad_e = int(self.end * sr)
        # Generate zero arrays
        start_samples = np.zeros(pad_s, dtype=np.float32)
        end_samples = np.zeros(pad_e, dtype=np.float32)
        # Concatenate arrays and return
        return np.concatenate((start_samples, data, end_samples), dtype=np.float32), sr
