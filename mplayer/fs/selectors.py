
from .. import config

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable
from abc import ABC, abstractmethod


class Selector(ABC):

    def select(self, new_paths: Iterable[Path] | Path) -> set[Path]:
        if isinstance(new_paths, Path):
            new_paths = [new_paths]
        return self._select(new_paths)

    @abstractmethod
    def _select(self, new_paths: Iterable[Path]) -> set[Path]:
        pass



class NewerThanSelector(Selector):

    def __init__(self, max_age: timedelta, clock=datetime.now):
        self._max_age = max_age
        self._clock = clock
        self._selected: set[Path] = set()

    def _select(self, new_paths):
        now = self._clock()
        cutoff = (now - self._max_age).timestamp()
        self._selected = {s for s in self._selected if s.stat().st_mtime > cutoff} | {p for p in new_paths if p.stat().st_mtime > cutoff}
        return self._selected


class LatestSelector(Selector):

    def __init__(self, count: int):
        self._count = count
        self._oldest = datetime.fromtimestamp(0)
        self._vals: set[Path] = set()

    def _select(self, new_paths) -> set[Path]:
        cutoff = self._oldest.timestamp()
        filtered = [p for p in new_paths if p.stat().st_mtime > cutoff]
        if filtered:
            values = [f for f in filtered] + list(self._vals)
            if len(values) > self._count:
                values.sort(key=lambda x: x.stat().st_mtime)
                values = values[-self._count:]
            self._vals = set(values)
        return self._vals

class PassThroughSelector(Selector):

    def __init__(self):
        self._set = set()

    def _select(self, new_paths) -> set[Path]:
        self._set |= set(new_paths)
        return self._set


class UnionSelector(Selector):

    def __init__(self, *selectors: Selector):
        self._selectors = selectors
        self._vals = set()

    def _select(self, new_paths) -> set[Path]:
        new_vals = set()
        for s in self._selectors:
            new_vals |= s._select(new_paths)
        self._vals = new_vals
        return self._vals

def _make_selector(cfg: config.Filter) -> Selector:
    if isinstance(cfg, config.FilterNewerThan):
        return NewerThanSelector(cfg.max_age)
    if isinstance(cfg, config.FilterNewest):
        return LatestSelector(cfg.count)

def make_selector(cfg: list[config.Filter]) -> Selector:
    if not cfg:
        return PassThroughSelector()
    selectors = [_make_selector(c) for c in cfg]
    if len(selectors) == 1:
        return selectors.pop()
    return UnionSelector(*selectors)
