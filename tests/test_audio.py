from __future__ import annotations

from glob import glob
from os.path import join
from unittest.mock import patch

import pytest

from nwave import Task, TaskException, audio


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
