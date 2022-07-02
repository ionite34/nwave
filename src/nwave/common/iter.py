from __future__ import annotations
from collections.abc import Generator, Callable
from functools import wraps
from typing import Sized


class Length:
    def __init__(self, length_like: int | Sized):
        self._length: int = 0
        self._call: Callable[None, int] | None = None

        if isinstance(length_like, int):
            self._length = length_like
        elif isinstance(length_like, Sized):
            self._call = length_like
        else:
            raise TypeError(
                f"Length must be an int or a Sized object, not {type(length_like)}"
            )

    @property
    def value(self) -> int:
        if self._call is not None:
            return self._call.__len__()
        return self._length


class SizedGenerator(Generator):
    def __init__(self, gen: Generator, length: int | Sized):
        """
        Generator with fixed size.

        Args:
            gen: Base Generator
            length: Length of iterator as int, or Sized object that implements __len__
        """
        super().__init__()
        if not isinstance(gen, Generator):
            raise TypeError(f"Expected Generator, got {type(gen)}")
        self._gen = gen
        self._length = Length(length)
        self._max = self._length.value  # Use first value to set max
        self._index = 0

    def send(self, *args, **kwargs):
        if self._index > self._length.value:
            self.throw(
                IndexError(f"Iteration out of range: {self._index}/{self._length}")
            )
        self._index += 1
        return self._gen.send(*args, **kwargs)

    def throw(self, *args, **kwargs):
        return self._gen.throw(*args, **kwargs)

    def __len__(self) -> int:
        return self._length.value - self._index


# Wrapper decorator for generators
def sized_generator(length: int | Sized | None = None):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return SizedGenerator(func(*args, **kwargs), length=length)

        return wrapper

    return deco
