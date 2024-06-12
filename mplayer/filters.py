from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


class Filter(ABC):

    @abstractmethod
    def __call__(self, paths: Iterable[Path]) -> Iterable[Path]:
        pass


class Newest(Filter):

    name = "newest"

    def __init__(self, count: int):
        super().__init__()
        self._c = count

    def __call__(self, paths: Iterable[Path]):
        s = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
        return s[: self._c]


def filter_by_name(nm: str):
    for candidate in [Newest]:
        if candidate.name == nm:
            return Newest
    raise ValueError(f"Unknown filter: {nm}")
