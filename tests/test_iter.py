from __future__ import annotations

from collections.abc import Sized
from typing import Generator

import pytest
from tqdm import tqdm

from nwave.common.iter import SizedGenerator, sized_generator


@pytest.fixture(scope="function")
def make_gen():
    size = 25

    @sized_generator(length=25)
    def _make_gen(size_in):
        yield from range(size_in)

    return _make_gen(size)


@pytest.mark.parametrize(
    "value, expected",
    [
        (1, True),  # int
        ([1, 2, 3], True),  # list
        (1.0, False),  # float
        ((x for x in range(3)), False),  # Generator
    ],
)
def test_length_like(value, expected):
    assert isinstance(value, (int, Sized)) == expected


def test_length_like_ex():
    # Make a generator
    gen = (i for i in range(3))
    # Try length
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        len(gen)
    # Generator should not be Sized
    assert not isinstance(gen, Sized)


def test_decorator(make_gen):
    # Check that it works as a decorator
    gen = make_gen
    assert isinstance(gen, Generator)
    assert isinstance(gen, SizedGenerator)
    assert isinstance(gen, Sized)
    assert hasattr(gen, "__len__")
    assert len(gen) == 25
    for i, v in enumerate(gen):
        assert v == i

    # Check out of range
    with pytest.raises(StopIteration):
        next(gen)

    # Check throw
    with pytest.raises(RuntimeError):
        gen.throw(RuntimeError)


def test_decorator_ex(make_gen):
    # Check invalid decorator use
    with pytest.raises(TypeError):

        @sized_generator(length=1)
        def _make_gen():
            return 1

        _make_gen()


def test_sized_gen():
    # Create a generator
    gen = (i for i in range(10))

    # Wrap it using with_len
    f_gen = SizedGenerator(gen, 10)

    # Check that it has __len__
    assert len(f_gen) == 10

    # Check that it works as a generator
    assert isinstance(f_gen, Generator)
    results = []
    for i in f_gen:
        results.append(i)
    assert results == list(range(10))


def test_sized_gen_ex():
    # Test wrong LengthLike type
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        SizedGenerator((i for i in range(5)), 1.0)


def test_fixed_gen_tqdm(capsys):
    # Create a generator and wrap it with FixedGenerator
    gen = (i for i in range(128))
    # Use list as LengthLike source
    f_gen = SizedGenerator(gen, list(range(128)))
    assert len(f_gen) == 128

    # Check that it works with tqdm
    counter = 0
    for i in tqdm(f_gen):
        counter += 1
    assert counter == 128
    captured = capsys.readouterr()
    assert "128/128" in captured.err


def test_show():
    gen = (i for i in range(128))
    f_gen = SizedGenerator(gen, 128)
    assert len(f_gen) == 128
