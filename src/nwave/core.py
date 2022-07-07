from __future__ import annotations

import os
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Iterator, TYPE_CHECKING

from .audio import process
from .common.iter import sized_generator
from .scheduler import Task, TaskResult

if TYPE_CHECKING:
    from .batch import Batch


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
    def n_tasks(self) -> int:
        """Number of tasks in queue"""
        return len(self._task_queue)

    def schedule(self, batch: Batch):
        """
        Submit a batch of tasks to the scheduler.

        Args:
            batch: Batch to schedule for running.
        """
        self._task_queue.extend(
            [(self._executor.submit(process, task), task) for task in batch.tasks]
        )

    def yield_all(
        self,
        timeout: float | None = None,
        per_task_timeout: bool = False,
    ) -> Iterator[TaskResult]:
        """
        Wait for all tasks to finish, process results as they come in.

        Args:
            timeout: Timeout in seconds before cancelling task.
                Set to 0 to cancel all in-progress tasks.
            per_task_timeout: True to apply timeout to each task, False to apply to entire batch.

        Returns:
            Sized Iterator of TaskResult
        """

        @sized_generator(len(self._task_queue))
        def gen():
            end_time = (timeout or 0) + time.monotonic()

            try:
                while self._task_queue:
                    ft: Future
                    task: Task
                    ft, task = self._task_queue.popleft()

                    if timeout is not None and not per_task_timeout:
                        task_exception = ft.exception(end_time - time.monotonic())
                    else:
                        task_exception = ft.exception(timeout)

                    if task_exception is None:
                        yield TaskResult(task, None)
                    else:
                        yield TaskResult(task, task_exception)
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
