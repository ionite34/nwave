import pytest
from unittest.mock import patch
from os import listdir
from os.path import join, exists
from tempfile import TemporaryDirectory

from nwave.interlocked.writer import Writer


# Normal write test
def test_writer():
    with TemporaryDirectory() as tmpdir:
        with Writer(join(tmpdir, "test.res")) as f:
            f.write(b"test")
        # Check that the file exists
        assert exists(join(tmpdir, "test.res"))


# Test that original file safe if overwrite fails due to mode
def test_writer_exceptions():
    # Load a temp directory
    with TemporaryDirectory() as tmpdir:
        # File is Directory error
        with pytest.raises(ValueError):
            with Writer(tmpdir) as f:
                f.write(b"test")
        # File exists error
        open(join(tmpdir, "exists.res"), 'w').write("test")
        assert exists(join(tmpdir, "exists.res"))
        with pytest.raises(FileExistsError):
            with Writer(join(tmpdir, "exists.res")) as f:
                f.write(b"test")
        # Check original file was not overwritten
        assert open(join(tmpdir, "exists.res")).read() == "test"
        # Check no temp file remains
        assert len(listdir(tmpdir)) == 1


# Test that the temp file is deleted if write fails due to exception
def test_writer_cleanup():
    with TemporaryDirectory() as tmpdir:
        # Patch os.rename to raise an error
        with patch('os.rename', side_effect=OSError):
            with pytest.raises(OSError):
                with Writer(join(tmpdir, 'test.res')) as f:
                    f.write(b"test")
        # Check that the temp file was deleted
        assert len(listdir(tmpdir)) == 0
