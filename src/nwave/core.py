from __future__ import annotations
import time
import typing as ty
from concurrent.futures import ThreadPoolExecutor, Future

import os
from collections import deque

from .scheduler import Task, TaskResult
from .audio import process
from .common.iter import sized_generator


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
            max_workers=self.threads, thread_name_prefix="WaveCore"
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._executor.shutdown(wait=self.exit_wait)
        return False

    @property
    def n_tasks(self):
        """Number of tasks in queue"""
        return len(self._task_queue)

    def schedule(self, batch: "Batch"):
        """
        Submit a batch of tasks to the scheduler.

        Args:
            batch: Batch to schedule for running.
        """
        self._task_queue.extend(
            [(self._executor.submit(process, task), task) for task in batch.tasks]
        )

    def yield_all(self, timeout: float = None) -> ty.Iterator[TaskResult]:
        """
        Wait for all tasks to finish, process results as they come in.

        Args:
            timeout: Timeout in seconds before cancelling task.
            Set to 0 to cancel all in-progress tasks.

        Returns:
            Sized Iterator of TaskResult
        """

        @sized_generator(len(self._task_queue))
        def gen():
            if timeout is not None:
                end_time = timeout + time.monotonic()

            try:
                while self._task_queue:
                    ft, task = self._task_queue.pop()

                    if timeout is None:
                        task_exception = ft.exception()
                    else:
                        task_exception = ft.exception(end_time - time.monotonic())

                    if task_exception is None:
                        yield TaskResult(task, True, None)
                    else:
                        yield TaskResult(task, False, task_exception)
            finally:
                # Cancel all remaining tasks
                for ft, task in self._task_queue:
                    ft.cancel()
                self._task_queue.clear()

        return gen()

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
