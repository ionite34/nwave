# Performance Profiling Tests
from __future__ import annotations
from joblib import Parallel, delayed
import asyncio
import os
import time

from tests_profile.resources import profile_audio as pa
from nwave import Task, Config
from tests_profile import data


class CleanUp:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Cleaning up")
        count = 0
        for _, out_f in data.enum(256):
            if os.path.exists(out_f):
                os.remove(out_f)
                count += 1
        if count:
            print(f"Removed {count} files")


class Time:
    def __init__(self, verbose=False):
        self.start = None
        self.end = None
        self.verbose = verbose

    def delta(self) -> float:
        return self.end - self.start

    @staticmethod
    def t_format(val: float) -> str:
        # Formats time to μs, ms, or s depending on the value
        if val >= 1:
            return f"{val:.2f} s"
        elif val >= 1e-3:
            val *= 1e3
            return f"{val:.2f} ms"
        else:
            val *= 1e6
            return f"{val:.2f} μs"

    def __enter__(self) -> Time:
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()
        if self.verbose:
            print(f"Elapsed: {self.t_format(self.delta())}")


def profile_audio(n_files: int):
    cfg = Config(
        sample_rate=44100,
        resample_quality='HQ',
        silence_padding=(950, 950),
    )
    with CleanUp():
        with Time(verbose=True):
            for i, (in_f, out_f) in enumerate(data.enum(n_files)):
                # print(f"Task[{i + 1}] {in_f} -> {out_f}")
                task = Task(in_f, out_f, cfg, overwrite=True)
                with Time(verbose=False):
                    pa.process_file(task)
                    # asyncio.run(pa.async_process_file(task))


def profile_audio_parallel(n_files: int, threads: int):
    cfg = Config(
        sample_rate=44100,
        resample_quality='HQ',
        silence_padding=(950, 950),
    )
    with CleanUp():
        with Time(verbose=True):
            tasks = [Task(in_f, out_f, cfg, overwrite=True) for in_f, out_f in data.enum(n_files)]

            def func(task):
                # asyncio.run(pa.async_process_file(task))
                pa.process_file(task)

            Parallel(
                n_jobs=threads,
                prefer='threads',
            )(delayed(func)(task) for task in tasks)


def main():
    n_files = 128
    print(f'{n_files} files')
    threads = 12
    print('[Single]')
    profile_audio(n_files)
    print('-' * 5)
    print(f'[Parallel] {threads} threads')
    profile_audio_parallel(n_files, threads)


if __name__ == '__main__':
    main()
