import pytest
from unittest.mock import patch
from os.path import join
from glob import glob
from nwave import audio, Task, TaskException


def test_process_write_exceptions(data_dir):
    # Find a file
    f = glob(join(data_dir, "*.wav"))[0]
    # Create a task
    t = Task(f, f, [], True)
    # Process os.rename to raise an exception
    with patch("os.rename", side_effect=OSError("Test")):
        with pytest.raises(TaskException) as e:
            audio.process(t)
        assert str(e.value) == "During File Writing -> OSError: Test"
