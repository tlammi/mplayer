import shutil
import tempfile
import contextlib

from pathlib import Path
from typing import Iterator


@contextlib.contextmanager
def persist(path: Path) -> Iterator[Path]:
    """
    Get a persistent handle to a file

    Create a persistent copy of the given file that is valid for the duration
    of the context manager. This effectively creates a temporary file with the
    same name with the same contents as the original file

    May throw FileNotFoundError if the file is deleted while being persisted
    """
    with tempfile.TemporaryDirectory() as d:
        dst = Path(d) / path.name
        shutil.copy(path, dst)
        yield dst
