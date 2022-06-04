# Example Audio Data
import glob
import os

DATA_PATH = os.path.dirname(os.path.realpath(__file__))


def enum(num_files: int) -> list[(str,  str)]:
    """
    Enumerates the files in the input directory
    """
    # Do a glob to get all wav files
    files = glob.glob(f"{DATA_PATH}/*.wav")

    if len(files) < num_files:
        raise ValueError(f"Not enough files in {DATA_PATH},"
                         f" expected {num_files}, found {len(files)}")

    for i, file in enumerate(files):
        if i >= num_files:
            break
        out_f = file.replace('.wav', '_out.wav')
        yield file, out_f
