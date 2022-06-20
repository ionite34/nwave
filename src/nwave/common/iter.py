from collections.abc import Generator, Callable
from functools import wraps
from typing import Union, Sized

LengthLike = Union[int, Sized]


class Length:
    def __init__(self, source: LengthLike):
        self._length: int = 0
        self._call: Callable[None, int] | None = None

        if isinstance(source, int):
            self._length = source
        elif isinstance(source, Sized):
            self._call = source
        else:
            raise TypeError(f'Length must be an int or a Sized object, not {type(source)}')

    @property
    def value(self):
        if self._call is not None:
            return self._call.__len__()
        return self._length


class SizedGenerator(Generator):
    def __init__(self, gen: Generator, length: LengthLike):
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
        self._index = 0

    def send(self, *args, **kwargs):
        if self._index > self._length.value:
            self.throw(IndexError(f"Index out of range: {self._index}. Length defined as {self._length}."))
        self._index += 1
        return self._gen.send(*args, **kwargs)

    def throw(self, *args, **kwargs):
        return self._gen.throw(*args, **kwargs)

    def __len__(self):
        return self._length.value


# Wrapper decorator for generators
def sized_generator(length: LengthLike = None):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return SizedGenerator(func(*args, **kwargs), length=length)

        return wrapper

    return deco
