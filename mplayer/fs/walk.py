import logging
import os

from pathlib import Path
from typing import Generator
from .full_match import full_match

_L = logging.getLogger(__name__)

def _do_walk(path: Path, ignore_dirs: bool):
    for parent, dirs, files in os.walk(path):
        par = Path(parent)
        yield from [par/f for f in files]
        if not ignore_dirs:
            yield from [par/d for d in dirs]

def _passes_filter(path: Path, filter: list[str], case_sensitive: bool|None):
    include = filter[0]
    if not full_match(path, include, case_sensitive=case_sensitive):
        return False
    exclude = filter[1:]
    if any(full_match(path, e, case_sensitive=case_sensitive) for e in exclude):
        return False
    return True

def _passes_filters(path: Path, filters: list[list[str]], case_sensitive: bool|None):
    for f in filters:
        if _passes_filter(path, f, case_sensitive):
            return True
    return False

def walk(path: Path, *, filters: list[str] | None = None, ignore_dirs=False, case_sensitive: bool|None=None) -> Generator[Path, None, None]:
    """
    Walk directory recursively and return all child items

    :param path Path to the root directory
    :param filters Glob strings to filter the events with. "+" prefix to include, "-" prefix to exclude.
    :param ignore_dirs Whether to skip directories
    :param case_sensitive Whether to ignore case when matching filters. Default is the platform default.

    :return Matching filesystem items found
    """
    sorted_filters = []
    for f in filters or []:
        if f.startswith("+"):
            sorted_filters.append([f[1:]])
        elif f.startswith("-"):
            sorted_filters[-1].append(f[1:])
        else:
            raise ValueError(f"Filter '{f}' does not start with + or '")
    for i in _do_walk(path, ignore_dirs):
        if _passes_filters(i, sorted_filters, case_sensitive):
            _L.debug("FS walk MATCH: %s", i)
            yield i.relative_to(path)
        else:
            _L.debug("FS walk MISS: %s", i)
