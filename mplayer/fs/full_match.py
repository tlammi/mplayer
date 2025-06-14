import fnmatch
import os

def full_match(path: os.PathLike, pattern: str, *, case_sensitive=None) -> bool:
    """
    Path.full_match is only available in python 3.12
    """
    if case_sensitive or case_sensitive is None:
        return fnmatch.fnmatchcase(str(path), pattern)
    return fnmatch.fnmatch(str(path), pattern)

