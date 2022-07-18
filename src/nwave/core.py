from __future__ import annotations

import os
import time
import typing as t
from collections import deque
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor

from .audio import process
from .common.iter import SizedGenerator
from .task import Task
from .task import TaskResult

if t.TYPE_CHECKING:
    from .batch import Batch  # pragma: no cover


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
        # Use new default threads algorithm (default for Py 3.8+)
        self.threads = threads or min(32, (os.cpu_count() or 1) + 4)
        self.exit_wait = exit_wait
        self._task_queue: deque[tuple[Future, Task]] = deque()

    def __enter__(self) -> WaveCore:
        """
        Enter context manager.

        Returns:
            WaveCore
        """
        self._executor = ThreadPoolExecutor(
            max_workers=self.threads, thread_name_prefix="WaveCore"
        )
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit context manager.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            traceback: Traceback
        """
        self._executor.shutdown(wait=self.exit_wait)

    @property
    def n_tasks(self) -> int:
        """
        Number of tasks currently in queue

        Returns:
            Number of tasks currently in queue
        """
        return len(self._task_queue)

    def schedule(self, batch: Batch) -> None:
        """
        Submit a batch of tasks to the scheduler.

        Args:
            batch: Batch to schedule for running.
        """
        self._task_queue.extend(
            [(self._executor.submit(process, task), task) for task in batch.tasks]
        )

    def yield_all(
        self, timeout: float | None = None, per_task_timeout: bool = False
    ) -> SizedGenerator:
        """
        Iterator for all scheduled tasks

        Args:
            timeout: Timeout in seconds before cancelling task.
                Set to 0 to cancel all in-progress tasks.
            per_task_timeout: True to apply timeout to each task,
                False to apply to entire batch.

        Returns:
            Sized Generator of TaskResult
        """

        def gen() -> t.Generator[TaskResult, None, None]:
            end_time = (timeout or 0) + time.monotonic()

            try:
                while self._task_queue:
                    future: Future
                    task: Task
                    future, task = self._task_queue.popleft()

                    if timeout is not None and not per_task_timeout:
                        task_exception = future.exception(end_time - time.monotonic())
                    else:
                        task_exception = future.exception(timeout)

                    if task_exception is None:
                        yield TaskResult(task, None)
                    else:
                        yield TaskResult(task, task_exception)
            finally:
                # Cancel all remaining tasks
                for future, task in self._task_queue:
                    future.cancel()
                self._task_queue.clear()

        return SizedGenerator(gen(), len(self._task_queue))

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
