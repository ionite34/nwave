# Task Data
from __future__ import annotations

import soundfile as sf
from dataclasses import dataclass

_sr = {8000, 16000, 32000, 44100, 48000}
_quality = {'QQ', 'LQ', 'MQ', 'HQ', 'VHQ'}
_format = set(sf.available_formats().keys())


@dataclass
class Config:
    """
    Transform effects and config

    None -> No Change from Source
    """
    # Output Sample Rate
    sample_rate: int = None
    # Resample Quality (One of 'QQ', 'LQ', 'MQ', 'HQ', 'VHQ')
    resample_quality: str = None
    # Silence padding in ms (start, end)
    silence_padding: (int, int) = (0, 0)
    # Output Channels
    channels: int = None
    # Output Bit-Depth
    format: str = None

    def frozen(self):
        """
        Return a frozen copy of the config.
        """
        return FrozenConfig(
            sample_rate=self.sample_rate,
            resample_quality=self.resample_quality,
            silence_padding=self.silence_padding,
            channels=self.channels,
            format=self.format
        )


@dataclass(frozen=True)
class FrozenConfig:
    """
    Transform effects and config

    None -> No Change from Source
    """
    # Output Sample Rate
    sample_rate: int = None
    # Resample Quality (One of 'QQ', 'LQ', 'MQ', 'HQ', 'VHQ')
    resample_quality: str = None
    # Silence padding in ms (start, end)
    silence_padding: (int, int) = (0, 0)
    # Output Channels
    channels: int = None
    # Output Bit-Depth
    format: str = None

    # Validation
    def __post_init__(self):

        if self.sample_rate and self.sample_rate not in _sr:
            raise ValueError(f'Invalid sample rate: {self.sample_rate}')

        if self.resample_quality and self.resample_quality not in _quality:
            raise ValueError(f'Invalid resample quality: {self.resample_quality}')

        if self.silence_padding:
            if not isinstance(self.silence_padding, tuple) or len(self.silence_padding) != 2:
                raise ValueError(f'Invalid silence padding: {self.silence_padding}')
            pad_start, pad_end = self.silence_padding
            if pad_start < 0 or pad_end < 0:
                raise ValueError(f'Invalid silence padding: {self.silence_padding}')

        if self.channels and self.channels not in {1, 2}:
            raise ValueError(f'Invalid channels: {self.channels}')

        if self.format and self.format not in _format:
            raise ValueError(f'Invalid format: {self.format}, available: {_format}')
