import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, wait, Future, CancelledError
# noinspection PyProtectedMember
from concurrent.futures._base import DoneAndNotDoneFutures

import os
from warnings import warn
from collections import deque
from typing import Iterable, Iterator
from .exceptions import TaskException
from .scheduler import Task, TaskResult
from .audio import process

# Named Tuple for task results
# TaskResult = namedtuple('TaskResult', ['task', 'success', 'error'])


class WaveCore(ThreadPoolExecutor):
    def __init__(self, threads: int = None, exit_wait: bool = True):
        """
        Processor for wave tasks.

        Args:
            threads: Number of threads to use.
                Defaults to min(32, os.cpu_count() + 4)
            exit_wait: Whether to wait for all tasks to finish before exiting context.
        """
        super().__init__()
        # Set threads to min(32, os.cpu_count() + 4) if not specified
        # This is default behavior since Python 3.8, but this will standardize behavior
        self.threads = threads or min(32, (os.cpu_count() or 1) + 4)
        self.exit_wait = exit_wait
        self._futures_queue: deque[Future] = deque()
        self._tasks_queue: deque[Task] = deque()

    def __enter__(self):
        self._executor = ThreadPoolExecutor(
            max_workers=self.threads,
            thread_name_prefix='WaveCore'
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._executor.shutdown(wait=self.exit_wait)
        return False

    @property
    def n_tasks(self):
        """ Number of tasks in queue """
        return len(self._tasks_queue)

    def schedule(self, tasks: Iterable[Task]):
        """
        Submit a batch of tasks to the scheduler.

        Args:
            tasks: Iterable of tasks to submit.
        """
        for task in tasks:
            if task.file_output in self._tasks_queue:
                raise ValueError("Output file already exists")
            ft = self._executor.submit(process, task)
            self._futures_queue.appendleft(ft)
            self._tasks_queue.appendleft(task)

    def submit(self, *tasks: Task):
        """
        Submit a batch of tasks to be run.

        Args:
            *tasks: Tasks to submit.

        Returns:
            A list of futures.
        """

    def yield_all(self, timeout: float = None) -> Iterator[TaskResult]:
        """
        Wait for all tasks to finish, process results as they come in.

        Args:
            timeout: Timeout in seconds before cancelling task.
            Set to 0 to cancel all in-progress tasks.

        Returns:
            Iterator of TaskResult
        """
        if timeout is not None:
            end_time = timeout + time.monotonic()

        while self._futures_queue:
            ft = self._futures_queue.pop()
            task = self._tasks_queue.pop()

            if timeout is None:
                task_exception = ft.exception()
            else:
                # noinspection PyUnboundLocalVariable
                task_exception = ft.exception(end_time - time.monotonic())

            if task_exception is None:
                yield TaskResult(task, True, None)
            elif isinstance(task_exception, (TaskException, CancelledError)):
                yield TaskResult(task, False, task_exception)
            else:
                warn(f"Unhandled Task exception during [{task}]: {task_exception}")
                yield TaskResult(task, False, task_exception)

    def wait_all(self, timeout: float = None) -> list[TaskResult]:
        """
        Wait for all tasks to finish, return as a list.

        Args:
            timeout: Timeout in seconds before cancelling task.
            Set to 0 to cancel all in-progress tasks.

        Returns:
            List of TaskResult
        """
        return list(self.yield_all(timeout))
