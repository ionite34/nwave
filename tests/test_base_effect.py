import pytest

# noinspection PyProtectedMember
from nwave._base import BaseEffect


def test_base_effect():
    # Create a subclass of BaseEffect
    class MyEffect(BaseEffect):
        def __init__(self):
            super().__init__()

        def _apply(self, dt1):
            return dt1

        def apply_trace(self, data):
            return self._apply(data)

    # Create an instance of MyEffect
    effect = MyEffect()
    assert isinstance(effect, MyEffect)
    assert isinstance(effect, BaseEffect)