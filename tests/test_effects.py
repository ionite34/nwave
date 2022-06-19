from collections import namedtuple
import math

import numpy as np
import pytest
import nwave.effects as fx
from nwave.exceptions import TaskException

# Named tuple of wave data
Wave = namedtuple('Wave', ['data', 'sr'])


# Fixture to load an example audio from librosa and return (array, sample rate)
@pytest.fixture(scope='module')
def wav() -> Wave:
    import librosa
    sample = librosa.example('trumpet')
    data, sr = librosa.load(sample)
    return data, sr


@pytest.mark.parametrize('target_sr, quality', [
    (int(44100), 'QQ'),
    (int(16050), 'LQ'),
    (float(44100), 'MQ'),
    (float(16050), 'HQ'),
    (float(22050.5), 'VHQ'),
])
def test_resample(wav, target_sr, quality):
    # Load data
    data, sr = wav
    # Test for Resample class
    effect = fx.Resample(target_sr, quality)
    assert effect.sample_rate == target_sr
    assert effect.quality == quality
    # Do the resample
    re_data, re_sr = effect.apply_trace(data, sr)
    assert re_sr == target_sr
    # We expect the data to be a factor of the original
    expected_factor = target_sr / sr
    factor = len(re_data) / len(data)
    assert math.isclose(factor, expected_factor, rel_tol=0.01)  # 1% tolerance


# Test Resample Exceptions
@pytest.mark.parametrize('target_sr, quality, ex', [
    (44100, 'NA', ValueError),
    (44100, 5, ValueError),
    ('A', 'HQ', ValueError),
])
def test_resample_exceptions(wav, target_sr, quality, ex):
    # Load data
    data, sr = wav
    # Test for Resample class
    with pytest.raises(ex):
        effect = fx.Resample(target_sr, quality)
        effect.apply_trace(data, sr)


# Test Resample Task Exception
def test_resample_exceptions_task(wav):
    # Load data
    data, sr = wav
    effect = fx.Resample(44100, 'HQ')
    effect.apply_trace(data, sr)
