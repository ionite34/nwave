import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, wait, Future, CancelledError
# noinspection PyProtectedMember
from concurrent.futures._base import DoneAndNotDoneFutures

import os
from queue import Queue
from collections import deque
from typing import Iterable, Iterator
from .scheduler import Task
from .audio import process_file

# Named Tuple for task results
TaskResult = namedtuple('TaskResult', ['task', 'success', 'error'])


class WaveCore:
    def __init__(self, n_threads: int = None, exit_wait: bool = True):
        """
        Processor for wave tasks.

        Args:
            n_threads: Number of threads to use.
                Defaults to min(32, os.cpu_count() + 4)
            exit_wait: Whether to wait for all tasks to finish before exiting context.
        """
        self._futures_queue: deque[Future] = deque()
        self._tasks_queue: deque[Task] = deque()
        self.exit_wait = exit_wait
        # Set threads to min(32, os.cpu_count() + 4) if not specified
        # This is default behavior since Python 3.8, but this will standardize behavior
        if n_threads is None:
            n_threads = min(32, os.cpu_count() + 4)

        self._executor = ThreadPoolExecutor(
            max_workers=n_threads,
            thread_name_prefix='WaveCore'
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._executor.shutdown(wait=self.exit_wait)
        return False

    @property
    def n_tasks(self):
        """ Number of tasks in queue """
        return len(self._tasks_queue)

    def submit(self, tasks: Iterable[Task]):
        """
        Submit a batch of tasks to the scheduler.

        Args:
            tasks: Iterable of tasks to submit.
        """
        for task in tasks:
            if task.file_output in self._tasks_queue:
                raise ValueError("Output file already exists")
            ft = self._executor.submit(process_file, task)
            self._futures_queue.appendleft(ft)
            self._tasks_queue.appendleft(task)

    def wait_all(self, timeout: float = None) -> Iterator[TaskResult]:
        """
        Wait for all tasks to finish, process results as they come in.

        Args:
            timeout: Timeout in seconds before cancelling task.
            Set to 0 to cancel all in-progress tasks.

        Returns:
            Iterator of TaskResult - a named tuple of (task, success, error)
        """
        if timeout is not None:
            end_time = timeout + time.monotonic()

        while self._futures_queue:
            ft = self._futures_queue.pop()
            task = self._tasks_queue.pop()

            if timeout is None:
                task_exception = ft.exception()
            else:
                task_exception = ft.exception(end_time - time.monotonic())

            if task_exception is None:
                yield TaskResult(task, True, None)
            else:
                yield TaskResult(task, False, task_exception)
