from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor

from colorama import Fore
from joblib import delayed
from joblib import Parallel
from tqdm import tqdm

from nwave import audio
from nwave import Batch
from nwave import effects
from nwave import Task
from nwave import WaveCore
from tests_profile import data


class CleanUp:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Search all files in directory with 'out' in the name
        count = 0
        for file in os.listdir(data.DATA_PATH):
            if "out" in file:
                os.remove(os.path.join(data.DATA_PATH, file))
                count += 1
        if count:
            print(f"[Clean-up] Removed {count} output files")


class Time:
    def __init__(self, verbose=False):
        self.start = 0
        self.end = 0
        self.verbose = verbose

    def delta(self) -> float:
        return self.end - self.start

    def delta_f(self) -> str:
        # Formats time to μs, ms, or s depending on the value
        val = self.delta()
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
            print(f"Elapsed: {Fore.YELLOW}{self.delta_f()}{Fore.RESET}")


def pa_single(n_files: int, fx, threads: int, batch_num: int):
    # Get a list of files
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        for batch in total:
            for in_f, out_f in batch:
                task = Task(in_f, out_f, fx, overwrite=True)
                audio.process(task)


def pa_joblib(n_files: int, fx, threads: int, batch_num: int):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        with Parallel(n_jobs=threads, backend="threading") as thread_pool:
            for batch in total:
                thread_pool(
                    delayed(audio.process)(Task(in_f, out_f, fx, overwrite=True))
                    for in_f, out_f in batch
                )


def pa_threadpool_submit(n_files: int, fx, threads: int, batch_num: int):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for batch in total:
                tasks = [
                    executor.submit(
                        audio.process, Task(in_f, out_f, fx, overwrite=True)
                    )
                    for in_f, out_f in batch
                ]
                for future in tasks:
                    if future.exception() is not None:
                        raise RuntimeError(future.exception())


def pa_threadpool_map(n_files: int, fx, threads: int, batch_num: int):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        with ThreadPoolExecutor(max_workers=threads) as thread_pool:
            for batch in total:
                jobs = [Task(in_f, out_f, fx, overwrite=True) for in_f, out_f in batch]
                thread_pool.map(audio.process, jobs)


def pa_nwave(n_files: int, fx, threads: int, batch_num: int):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        with WaveCore(threads=threads) as core:
            for batch in total:
                in_files, out_files = zip(*batch)
                wave_batch = Batch(in_files, out_files, overwrite=True).apply(*fx)
                core.schedule(wave_batch)


def pa_nwave_run(n_files: int, fx, threads: int, batch_num: int):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        for batch in total:
            in_files, out_files = zip(*batch)
            wave_batch = Batch(in_files, out_files, overwrite=True).apply(*fx)
            wave_batch.run(threads)


def pa_nwave_tqdm(n_files: int, fx, threads: int, batch_num: int):
    total = data.enum_batch(n_files, batch_num)
    with WaveCore(threads=threads) as core:
        for batch in total:
            in_files, out_files = zip(*batch)
            wave_batch = Batch(in_files, out_files, overwrite=True).apply(*fx)
            core.schedule(wave_batch)
            futures = core.yield_all()
            list(tqdm(futures))


def clean_up():
    # Search all files in directory with 'out' in the name
    count = 0
    for file in os.listdir(data.DATA_PATH):
        if "out" in file:
            os.remove(os.path.join(data.DATA_PATH, file))
            count += 1
    if count:
        print(f"{Fore.LIGHTBLACK_EX}[Clean-up] > Removed {count} files")


def main():
    fx = [effects.Resample(44100, quality="HQ"), effects.PadSilence(0.5, 0.5)]

    # Total operations = n_files * runs
    n_files = 900
    runs = 1
    threads = 20
    print(f"{n_files} files, {runs} batches")

    test_targets = [
        pa_single,
        pa_joblib,
        pa_threadpool_submit,
        pa_threadpool_map,
        pa_nwave,
        pa_nwave_run,
        pa_nwave_tqdm,
    ]

    for target in test_targets:
        print(f"{Fore.BLUE}Testing [{target.__name__}]{Fore.RESET}")
        target(n_files, fx, threads, runs)
        clean_up()


if __name__ == "__main__":
    main()
