import pytest
import os
import gzip
import tempfile
from importlib.resources import files

from . import data


@pytest.fixture(scope="function")
def data_dir():
    """
    Duplicates test .wav files and returns temp directory
    """
    n_copies = 5
    wav_zip = str(files(data).joinpath("sample.wav.gz"))
    with tempfile.TemporaryDirectory() as tmpdir, gzip.open(wav_zip, 'rb') as f:
        read_data = f.read()
        for i in range(n_copies):
            target = os.path.join(tmpdir, f'test_{i}.wav')
            with open(target, 'wb') as out:
                out.write(read_data)
        yield tmpdir
