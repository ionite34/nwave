from collections.abc import Generator, Callable
from functools import wraps
from typing import Union, Sized

LengthLike = Union[int, Sized]


class Length:
    def __init__(self, length: LengthLike):
        self._length: int = 0
        self._call: Callable[None, int] | None = None

        if isinstance(length, int):
            self._length = length
        elif isinstance(length, Sized):
            self._call = length
        else:
            raise TypeError(f'Length must be an int or a Sized object, not {type(length)}')


class SizedGenerator(Generator):
    def __init__(self, gen: Generator, length: LengthLike):
        """
        Generator with fixed size.

        Args:
            gen: Base Generator
            length: Length of iterator
        """
        super().__init__()
        if not isinstance(gen, Generator):
            raise TypeError(f"Expected Generator, got {type(gen)}")
        self._gen = gen
        self._length = length
        self._index = 0

    def send(self, *args, **kwargs):
        if self._index > self._length:
            self.throw(IndexError(f"Index out of range: {self._index}. Length defined as {self._length}."))
        self._index += 1
        return self._gen.send(*args, **kwargs)

    def throw(self, *args, **kwargs):
        return self._gen.throw(*args, **kwargs)

    def __len__(self):
        return self._length


# Wrapper decorator for generators
def fixed_generator(length: LengthLike = None):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return SizedGenerator(func(*args, **kwargs), length=length)

        return wrapper

    return deco
