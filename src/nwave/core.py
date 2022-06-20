import time
from concurrent.futures import ThreadPoolExecutor, Future, CancelledError

import os
from warnings import warn
from collections import deque
from typing import Iterable, Iterator
from .scheduler import Task, TaskResult, TaskException
from .audio import process


class WaveCore:
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
        self._task_queue: deque[(Future, Task)] = deque()

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
        return len(self._task_queue)

    def schedule(self, tasks: Iterable[Task]):
        """
        Submit a batch of tasks to the scheduler.

        Args:
            tasks: Iterable of tasks to submit.
        """
        for task in tasks:
            ft = self._executor.submit(process, task)
            self._task_queue.appendleft((ft, task))

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

        try:
            while self._task_queue:
                ft, task = self._task_queue.pop()

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
        finally:
            # Cancel all remaining tasks
            for ft, task in self._task_queue:
                ft.cancel()

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
