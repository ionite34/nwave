import pytest
from nwave.scheduler.config import Config, FrozenConfig


def test_config():
    config = Config()
    assert config.format is None
    assert config.sample_rate is None


@pytest.mark.parametrize('arg, expect_exception', [
    ({'sample_rate': 32000}, False),
    ({'sample_rate': -1000}, True),
    ({'resample_quality': 'QQ'}, False),
    ({'resample_quality': 'UQ'}, True),
    ({'silence_padding': (-1000, 0)}, True),
    ({'silence_padding': (0, -1000)}, True),
    ({'channels': 5}, True),
    ({'format': 'FLOAT'}, True),
])
def test_config_frozen(arg, expect_exception):
    # Basic config creation should always work
    config = Config(**arg)
    if expect_exception:
        # For case of bad value, raise exception on frozen convert
        with pytest.raises(ValueError):
            config.frozen()
    else:
        assert isinstance(config.frozen(), FrozenConfig)
