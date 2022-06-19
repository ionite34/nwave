import pytest

from nwave.scheduler import task


def test_task_exception():
    # Create a TaskException
    te = task.TaskException(ValueError('test'))
    print(type(te))
    print(te)
    assert isinstance(te, task.TaskException)
    with pytest.raises(task.TaskException):
        raise te


def test_task():
    # Create a Task
    t = task.Task('src.wav', 'dst.wav', [], True)

