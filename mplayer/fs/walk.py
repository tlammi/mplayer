import logging

from pathlib import Path
from typing import Generator

_L = logging.getLogger(__name__)

def _do_walk(path: Path, ignore_dirs: bool):
    for parent, dirs, files in path.walk():
        yield from [parent/f for f in files]
        if not ignore_dirs:
            yield from [parent/d for d in dirs]

def _passes_filter(path: Path, filter: str, case_sensitive: bool|None):
    if filter.startswith("+"):
        return path.full_match(filter[1:], case_sensitive=case_sensitive)
    if filter.startswith("-"):
        return not path.full_match(filter[1:], case_sensitive=case_sensitive)
    raise ValueError(f"Filter '{filter}' does not start with '+' or '-'")

def _passes_filters(path: Path, filters: list[str], case_sensitive: bool|None):
    for f in filters:
        if not _passes_filter(path, f, case_sensitive):
            return False
    return True

def walk(path: Path, *, filters: list[str] | None = None, ignore_dirs=False, case_sensitive: bool|None=None) -> Generator[Path]:
    """
    Walk directory recursively and return all child items

    :param path Path to the root directory
    :param filters Glob strings to filter the events with. "+" prefix to include, "-" prefix to exclude.
    :param ignore_dirs Whether to skip directories
    :param case_sensitive Whether to ignore case when matching filters. Default is the platform default.

    :return Matching filesystem items found
    """
    filters = filters or []
    for i in _do_walk(path, ignore_dirs):
        _L.debug("Walk reached file: %s", i)
        if _passes_filters(i, filters, case_sensitive):
            _L.debug("Walk matched file: %s", i)
            yield i
