# Example Audio Data
import glob
import os
from typing import Iterator

DATA_PATH = os.path.dirname(os.path.realpath(__file__))


def enum(num_files: int) -> Iterator:
    """
    Enumerates the files in the input directory
    """
    # Do a glob to get all wav files
    files = glob.glob(f"{DATA_PATH}/*.wav")

    if len(files) < num_files:
        raise ValueError(
            f"Not enough files in {DATA_PATH},"
            f" expected {num_files}, found {len(files)}"
        )

    for i, file in enumerate(files):
        if i >= num_files:
            break
        out_f = file.replace(".wav", "_out.wav")
        yield file, out_f


def enum_batch(per_batch: int, batches: int) -> list[list[(str, str)]]:
    """
    Enumerates the files in the input directory, splitting into batches
    """
    # Do a glob to get all wav files
    files = glob.glob(f"{DATA_PATH}/*.wav")

    total_files = per_batch * batches

    if len(files) < total_files:
        raise ValueError(
            f"Not enough files in {DATA_PATH},"
            f" expected {per_batch}, found {len(files)}"
        )

    result = []
    for i in range(batches):
        batch = []
        for j in range(per_batch):
            file = files[i * per_batch + j]
            out_f = file.replace(".wav", "_out.wav")
            batch.append((file, out_f))
        result.append(batch)

    return result
