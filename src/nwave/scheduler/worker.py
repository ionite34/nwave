from dask.distributed import Client


class Worker:
    def __init__(self, threads=1):
        self.client = Client(n_workers=threads)
