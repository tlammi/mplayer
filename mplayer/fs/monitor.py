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
    def __init__(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue[Event], filters: list[str] | None, ignore_dirs: bool):
        super().__init__()
        self._loop = loop
        self._queue = queue
        self._filters = filters or []
        self._ignore_dirs = ignore_dirs
        for f in self._filters:
            if not f.startswith("+") and not f.startswith("-"):
                raise ValueError(f"Filter '{f}' does not start with '+' or '-'")

    def on_any_event(self, event: FileSystemEvent) -> None:
        if self._ignore_dirs and event.is_directory:
            return
        evt = Event.from_fs_event(event)
        for f in self._filters:
            if f.startswith("+"):
                if not evt.src.full_match(f[1:]):
                    return
            elif f.startswith("-"):
                if evt.src.full_match(f[1:]):
                    return
        self._loop.call_soon_threadsafe(self._queue.put_nowait, evt)

async def monitor(path: PurePath | str, *, filters: list[str] | None = None, recursive=False, ignore_dirs=False) -> AsyncGenerator[Event]:
    q = asyncio.Queue[Event]()
    handler = _EventHandler(asyncio.get_running_loop(), q, filters, ignore_dirs)
    obs = Observer()
    obs.schedule(handler, str(path), recursive=recursive)
    obs.start()
    while True:
        yield await q.get()

