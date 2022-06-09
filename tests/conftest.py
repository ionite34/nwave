import pytest
import os
import shutil
import tempfile
import librosa


@pytest.fixture(scope="function")
def data_dir():
    """
    Copies test .wav files from librosa and returns temp directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download test .wav files
        sample = librosa.example('trumpet')
        # Copy file duplicated 5 times to temp directory
        for i in range(5):
            target = os.path.join(tmpdir, f'test_{i}.wav')
            shutil.copy(sample, target)
        assert len(os.listdir(tmpdir)) == 5
        yield tmpdir
