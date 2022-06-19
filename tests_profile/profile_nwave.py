# Performance Profiling Tests
from __future__ import annotations

import os
import time
from concurrent import futures
from concurrent.futures import ThreadPoolExecutor

from joblib import Parallel, delayed
from tqdm.auto import tqdm

from nwave import Task, effects, audio, WaveCore, Batch
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


def profile_audio(n_files: int, cfg, batch_num: int = 1):
    # Get a list of files
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        for batch in tqdm(total):
            for in_f, out_f in batch:
                task = Task(in_f, out_f, cfg, overwrite=True)
                audio.process(task)


def profile_audio_parallel(n_files: int, cfg, threads: int, batch_num: int = 1):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        with Parallel(n_jobs=threads, backend='threading') as thread_pool:
            for batch in total:
                thread_pool(delayed(audio.process)(
                    Task(in_f, out_f, cfg, overwrite=True)
                ) for in_f, out_f in batch)


def profile_audio_threadpool(n_files: int, cfg, threads: int, batch_num: int = 1):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        with ThreadPoolExecutor(max_workers=threads) as executor:
            for batch in total:
                tasks = {executor.submit(
                    audio.process, Task(in_f, out_f, cfg, overwrite=True)
                ): (in_f, out_f) for (in_f, out_f) in batch}
            # Wait for all tasks to complete
            for future in tqdm(futures.as_completed(tasks)):
                if future.done():
                    pass
                    # print(future.result())
                if future.exception():
                    print(future.exception())


def profile_audio_thread_map(n_files: int, cfg, threads: int, batch_num: int = 1):
    total = data.enum_batch(n_files, batch_num)
    with Time(verbose=True):
        with ThreadPoolExecutor(max_workers=threads) as thread_pool:
            for batch in total:
                jobs = [Task(in_f, out_f, cfg, overwrite=True) for in_f, out_f in batch]
                thread_pool.map(audio.process, jobs)


def profile_audio_nwave(n_files: int, cfg, threads: int, batch_num: int = 1):
    with WaveCore(n_threads=threads) as core:
        for batch in data.enum_batch(n_files, batch_num):
            for in_f, out_f in batch:
                task = Task(in_f, out_f, cfg, overwrite=True)
                core.schedule([task])
        with Time(verbose=True):
            core.wait_all()


def profile_audio_nwave_cus(n_files: int, cfg, threads: int, batch_num: int = 1):
    with WaveCore(n_threads=threads) as core:
        in_files = []
        out_files = []
        for batch in data.enum_batch(n_files, batch_num):
            for in_f, out_f in batch:
                in_files.append(in_f)
                out_files.append(out_f)
            batch = Batch(in_files, out_files, overwrite=True)
            batch = batch.apply(
                effects.Resample(44100, quality='HQ'),
                effects.PadSilence(0.5, 0.5)
            ).export()
        with Time(verbose=True):
            core.schedule(batch)
            core.wait_all()


def clean_up():
    print("Cleaning up")
    # Search all files in directory with 'out' in the name
    count = 0
    for file in os.listdir(data.DATA_PATH):
        if "out" in file:
            os.remove(os.path.join(data.DATA_PATH, file))
            count += 1
    if count:
        print(f"Removed {count} files")


def main():
    fx = [
        effects.Resample(44100, quality='HQ'),
        effects.PadSilence(0.5, 0.5)
    ]

    n_files = 64
    runs = 15
    threads = 20
    print(f'{n_files} files, {runs} batches')

    print('[Single]')
    # profile_audio(n_files, fx, batch_num=runs)
    print('-' * 3)
    clean_up()
    time.sleep(1)

    print('-' * 5)
    print(f'[Parallel] {threads} threads')
    # profile_audio_parallel(n_files, fx, threads, batch_num=runs)
    print('-' * 3)
    clean_up()
    time.sleep(1)

    print('-' * 5)
    print(f'[Parallel (Threadpool)] {threads} threads')
    # profile_audio_threadpool(n_files, fx, threads, batch_num=runs)
    print('-' * 3)
    clean_up()
    time.sleep(1)

    print('-' * 5)
    print(f'[Parallel (Thread Map)] {threads} threads')
    # profile_audio_thread_map(n_files, fx, threads, batch_num=runs)
    print('-' * 3)
    clean_up()
    time.sleep(1)

    print('-' * 5)
    print(f'[Parallel (NWave)] {threads} threads')
    # profile_audio_nwave(n_files, fx, threads, batch_num=runs)
    print('-' * 3)
    clean_up()
    time.sleep(1)

    print('-' * 5)
    print(f'[Parallel (NWave with Batch)] {threads} threads')
    profile_audio_nwave_cus(n_files, fx, threads, batch_num=runs)
    print('-' * 3)
    clean_up()
    time.sleep(1)


if __name__ == '__main__':
    # clean_up()
    main()
