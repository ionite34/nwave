import joblib
from dask.distributed import Client, as_completed
import dask.bag as db
from .engine import Task
from .audio import process_file, process_ffmpeg


class WaveCore:
    """
    WaveCore Class for Audio Processing Node
    """

    def __init__(self, n_workers=None, threads_per_worker=None, **kwargs):
        self.client = Client(
            n_workers=n_workers,
            threads_per_worker=threads_per_worker,
            processes=False,
            memory_limit='4GB',
            **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.close()

    def __del__(self):
        self.client.close()

    async def wait_all(self):
        # Wait for all tasks to finish
        pass

    def process_bag(self, tasks: list[Task]):
        b = db.from_sequence(tasks)
        res = db.map(process_file, b).compute()
        return res

    def process_bag_ffmpeg(self, tasks: list[Task]):
        b = db.from_sequence(tasks)
        res = db.map(process_ffmpeg, b).compute()
        return res

    def process(self, tasks: list[Task]):
        seq = self.client.map(process_file, tasks, pure=False)
        return self.client.gather(seq)

    def process_job(self, tasks: list[Task]):
        with joblib.parallel_backend('dask'):
            joblib.Parallel()(
                joblib.delayed(process_file)(task) for task in tasks
            )
