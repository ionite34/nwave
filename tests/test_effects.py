from __future__ import annotations

import gzip
import math
from importlib.resources import path

import pytest
import soxr
from scipy.io import wavfile

import nwave.effects as fx
from . import data as test_data
from nwave import TaskException


# Fixture to load an example audio and return (array, sample rate)
@pytest.fixture(scope="module")
def wav():
    with path(test_data, "sample.wav.gz") as p, gzip.open(p, "rb") as f:
        sr, arr = wavfile.read(f)
        return arr, sr


@pytest.mark.parametrize(
    "target_sr, quality",
    [
        (int(22050), "HQ"),  # No change path
        (int(44100), "QQ"),
        (int(16050), "LQ"),
        (float(44100), "MQ"),
        (float(16050), "HQ"),
        (float(22050.5), "VHQ"),
    ],
)
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
@pytest.mark.parametrize(
    "target_sr, quality, ex",
    [
        (44100, "NA", ValueError),
        (44100, 5, ValueError),
        ("A", "HQ", ValueError),
    ],
)
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
    effect = fx.Resample(44100, "HQ")
    effect.apply_trace(data, sr)


# Padding
def test_pad_silence(wav):
    # Load data
    data, sr = wav
    # Test for Pad class
    effect = fx.PadSilence(0.25, 0.25)
    out_data, out_sr = effect.apply_trace(data, sr)
    assert out_sr == sr
    # See if length has been correctly extended
    original_time = len(data) / sr
    res_time = len(out_data) / sr
    # Expect 5 seconds of padding, with 1% tolerance
    assert math.isclose(res_time, original_time + 0.5, rel_tol=0.01)


def test_pad_silence_exceptions(wav):
    # Non-positive padding
    with pytest.raises(ValueError):
        fx.PadSilence(-1, 0.25)


# Wrapper
def test_wrapper(wav):
    # Create a test effect using soxr resample
    # Do not supply data arg, try as positional argument
    effect = fx.Wrapper(
        soxr.resample,
        sr_arg="in_rate",
        output_sr_override=48500,
        out_rate=48500,
        quality="MQ",
    )
    # Load data
    data, sr = wav
    assert sr == 22050
    # Do the resample
    re_data, re_sr = effect.apply_trace(data, sr)
    assert re_sr == 48500
    # We expect the data to be a factor of the original
    expected_factor = 48500 / sr
    factor = len(re_data) / len(data)
    assert math.isclose(factor, expected_factor, rel_tol=0.01)  # 1% tolerance


# Wrapper ordering
def test_wrapper_ordering(wav):
    data, sr = wav

    def in_order(x, in_rate):
        return x, in_rate

    def rev_order(x, in_rate):
        return in_rate, x

    # Without override
    def no_override(x, in_rate):
        return x

    effect = fx.Wrapper(no_override, data_arg="x", sr_arg="in_rate")
    assert effect.apply_trace(data, sr) == (data, sr)

    # In order
    effect = fx.Wrapper(in_order, data_arg="x", sr_arg="in_rate")
    result = effect.apply_trace(data, sr)
    assert result == (data, sr)

    # Reversed order, but output should be the same
    effect = fx.Wrapper(rev_order, data_arg="x", sr_arg="in_rate")
    result = effect.apply_trace(data, sr)
    assert result == (data, sr)


def test_wrapper_exceptions(wav):
    # Not callable
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        fx.Wrapper(1, data_arg="x", sr_arg="in_rate")

    # Wrong return type
    def target(x_1):
        return 1.0

    with pytest.raises(TaskException) as exc_info:
        effect = fx.Wrapper(target, data_arg="x_1")
        effect.apply_trace(wav[0], wav[1])
    assert "got float" in str(exc_info.value)
