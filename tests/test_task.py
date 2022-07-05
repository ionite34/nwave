from concurrent.futures import CancelledError

import pytest

from nwave.scheduler import task


def test_task():
    # Create a Task
    t = task.Task("src.wav", "dst.wav", [], True)
    assert isinstance(t, task.Task)


def test_task_result():
    # Check basic creation of TaskResult
    t = task.Task("src.wav", "dst.wav", [], True)
    tr = task.TaskResult(t, None)
    assert isinstance(tr, task.TaskResult)
    assert tr.success
    assert tr.error is None

    # Check str representation
    assert str(tr) == "Task: src.wav -> dst.wav\n[Completed]"

    # Check str for canceled task
    tr = task.TaskResult(t, CancelledError())
    assert str(tr) == "Task: src.wav -> dst.wav\n[Cancelled]"

    # Check str for failed task
    tr = task.TaskResult(t, ValueError("test"))
    assert str(tr) == "Task: src.wav -> dst.wav\n[Failed]: test"


def test_task_exception():
    # Create a TaskException
    te = task.TaskException(ValueError("VE"))
    assert str(te) == "VE"
    with pytest.raises(task.TaskException):
        raise te

    # Test raising info
    te = task.TaskException(ValueError("VE"), during="Step-1")
    try:
        raise te
    except task.TaskException as e:
        assert str(e) == "During Step-1 -> ValueError: VE"
