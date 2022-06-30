from nwave.base import BaseEffect


def test_base_effect():
    # Create a subclass of BaseEffect
    class MyEffect(BaseEffect):
        def __init__(self):
            super().__init__()

        def apply(self, data, sr):
            return data, sr

        def apply_trace(self, data, sr):
            return self.apply(data, sr)

    # Create an instance of MyEffect
    effect = MyEffect()
    assert isinstance(effect, MyEffect)
    assert isinstance(effect, BaseEffect)
    assert effect.name == 'MyEffect'
