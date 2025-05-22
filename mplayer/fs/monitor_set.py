from pathlib import PurePath

from . import Event, EventType

class MonitorSet:

    def __init__(self, initial: set[PurePath]|None = None):
        self._static = initial or set()
        self._removed = set()
        self._new = set()
        self._modified = set()

    def add(self, evt: Event):
        Typ = EventType
        if evt.kind == Typ.Created:
            self._new.add(evt.src)
            self._removed.discard(evt.src)
            self._static.discard(evt.src)
            self._modified.discard(evt.src)
        elif evt.kind == Typ.Deleted:
            self._removed.add(evt.src)
            self._new.discard(evt.src)
            self._static.discard(evt.src)
            self._modified.discard(evt.src)
        elif evt.kind == Typ.Modified:
            self._modified.add(evt.src)
            self._new.discard(evt.src)
            self._static.discard(evt.src)
            self._removed.discard(evt.src)
        elif evt.kind == Typ.Moved:
            self._static.discard(evt.src)
            self._static.add(evt.dst)

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

    @property
    def removed(self):
        return self._removed

    @property
    def new(self):
        return self._new

    @property
    def modified(self):
        return self._modified
