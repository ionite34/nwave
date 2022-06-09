# Interlocked Write Handle
from __future__ import annotations

import os
from os import PathLike
import tempfile


class Writer:
    def __init__(self, file: str | PathLike):
        if os.path.isdir(file):
            raise ValueError(f"{file} cannot be a directory")
        self.file = file
        self.temp = tempfile.NamedTemporaryFile(
            delete=False,
            dir=os.path.dirname(self.file),
            mode='w+b'
        )

    def __enter__(self):
        # Return the opened file
        return self.temp

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close temp file
        self.temp.close()
        # If target file exists, delete it
        if os.path.isfile(self.file):
            os.remove(self.file)
        # Copy temp file to target (rename)
        os.rename(self.temp.name, self.file)
