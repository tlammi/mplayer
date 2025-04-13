import asyncio
from typing import AsyncGenerator
from pathlib import PurePath
from enum import Enum
from dataclasses import dataclass

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import watchdog.events as evts


class EventType(Enum):
    Moved = evts.EVENT_TYPE_MOVED
    Deleted = evts.EVENT_TYPE_DELETED
    Created = evts.EVENT_TYPE_CREATED
    Modified = evts.EVENT_TYPE_MODIFIED
    Closed = evts.EVENT_TYPE_CLOSED
    ClosedNoWrite = evts.EVENT_TYPE_CLOSED_NO_WRITE
    Opened = evts.EVENT_TYPE_OPENED

@dataclass
class Event:
    """
    File system event

    src: Source path. Always populated
    dst: Destination path. Populated if fitting
    kind: Event type
    is_directory: Whether the event target is a directory
    """
    src: PurePath
    dst: PurePath
    kind: EventType
    is_directory: bool

    @staticmethod
    def from_fs_event(evt: FileSystemEvent) -> "Event":
        assert isinstance(evt.src_path, str)
        assert isinstance(evt.dest_path, str)
        src = PurePath(evt.src_path)
        dst = PurePath(evt.dest_path)
        return Event(src=src, dst=dst, kind=EventType(evt.event_type), is_directory=evt.is_directory)

class _EventHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue[Event], root: PurePath, filters: list[str] | None, ignore_dirs: bool, event_types: set[EventType], case_sensitive: bool|None):
        super().__init__()
        self._loop = loop
        self._queue = queue
        self._root = root
        self._filters = filters or []
        self._ignore_dirs = ignore_dirs
        self._type_mask = event_types
        self._case_sensitive = case_sensitive
        for f in self._filters:
            if not f.startswith("+") and not f.startswith("-"):
                raise ValueError(f"Filter '{f}' does not start with '+' or '-'")

    def on_any_event(self, event: FileSystemEvent) -> None:
        if self._ignore_dirs and event.is_directory:
            return
        evt = Event.from_fs_event(event)
        if evt.kind not in self._type_mask:
            return
        if evt.src != PurePath():
            evt.src = evt.src.relative_to(self._root)
        if evt.dst != PurePath():
            evt.dst = evt.dst.relative_to(self._root)
        for f in self._filters:
            if f.startswith("+"):
                if not evt.src.full_match(f[1:], case_sensitive=self._case_sensitive):
                    return
            elif f.startswith("-"):
                if evt.src.full_match(f[1:], case_sensitive=self._case_sensitive):
                    return
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, evt)
        except RuntimeError:
            # The event loop might have been closed
            pass

async def monitor(path: PurePath, *, filters: list[str] | None = None, recursive=False, ignore_dirs=False, events: set[EventType] | None = None, case_sensitive: bool|None=None) -> AsyncGenerator[Event]:
    """
    Monitor path for changes

    :param path Path to the root directory
    :param filters Glob strings to filter the events with. "+" prefix to include, "-" prefix to exclude.
    :param recursive Whether to watch for changes recursively
    :param ignore_dirs Whether to exclude events regarding directories
    :param events Only emit events with these types. Default (None) means all
    :param case_sensitive Whether to ignore case when matching filters. Default is the platform default.

    :return Stream of filesystem events after filtering. The paths are relative to path
    """
    if events is None:
        events = {t for t in EventType}
    q = asyncio.Queue[Event]()
    handler = _EventHandler(asyncio.get_running_loop(), q, path, filters, ignore_dirs, events, case_sensitive)
    obs = Observer()
    obs.schedule(handler, str(path), recursive=recursive)
    obs.start()
    while True:
        yield await q.get()

