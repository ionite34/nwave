from __future__ import annotations
import os
from os import PathLike
import tempfile


class Writer:
    def __init__(self, file: str | PathLike, overwrite: bool = False):
        if os.path.isdir(file):
            raise ValueError(f"{file} cannot be a directory")
        self.file = file
        self.overwrite = overwrite
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
        try:
            # If target file exists
            if os.path.isfile(self.file):
                # Raise error if overwrite is False
                if not self.overwrite:
                    raise FileExistsError(f"File {self.file} already exists")
                os.remove(self.file)
            # Copy temp file to target (rename)
            os.rename(self.temp.name, self.file)
        finally:
            # Delete temp file
            if os.path.exists(self.temp.name):
                os.remove(self.temp.name)
