import pytest

from nwave.engine.task import Config


def test_config():
    config = Config()
    assert config.format is None
    assert config.sample_rate is None

    with pytest.raises(ValueError):
        Config(sample_rate=-500)
