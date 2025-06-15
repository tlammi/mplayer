from pathlib import Path
from datetime import datetime

from . import Event, EventType
from .. import config

class MonitorSet:

    def __init__(self, initial: set[Path]|None = None):
        self._static = initial or set()
        self._removed = set()
        self._new = set()
        self._modified = set()

    def add(self, evt: Event):
        Typ = EventType
        if evt.kind == Typ.Created:
            self._new.add(Path(evt.src))
            self._removed.discard(Path(evt.src))
            self._static.discard(Path(evt.src))
            self._modified.discard(Path(evt.src))
        elif evt.kind == Typ.Deleted:
            self._removed.add(Path(evt.src))
            self._new.discard(Path(evt.src))
            self._static.discard(Path(evt.src))
            self._modified.discard(Path(evt.src))
        elif evt.kind == Typ.Modified:
            self._modified.add(Path(evt.src))
            self._new.discard(Path(evt.src))
            self._static.discard(Path(evt.src))
            self._removed.discard(evt.src)
        elif evt.kind == Typ.Moved:
            self._static.discard(Path(evt.src))
            self._static.add(Path(evt.dst))

    def reset(self):
        self._static -= self._removed
        self._static |= self._new
        self._static |= self._modified
        self._removed = set()
        self._new = set()
        self._modified = set()

    @property
    def static(self):
        return self._static

    def filter_static(self, rule: config.Filter):
        if isinstance(rule, config.FilterNewest):
            if rule.count >= len(self._static):
                return
            new = sorted(self._static, key=lambda x: x.stat().st_mtime)
            self._static = set(new[-rule.count:])
            return
        if isinstance(rule, config.FilterNewerThan):
            cut_off = (datetime.now() - rule.max_age).timestamp()
            self._static = {s for s in self._static if s.stat().st_mtime > cut_off}
        raise TypeError(f"Unsupported filter: {type(rule)}")

    @property
    def removed(self):
        return self._removed

    @property
    def new(self):
        return self._new

    @property
    def modified(self):
        return self._modified
