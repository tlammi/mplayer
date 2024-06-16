"""
Program core
"""

import asyncio
import logging

from pathlib import Path
from typing import AsyncGenerator, Iterable
from .ctx import Ctx
from .playlist import PlaylistSpec, Playlist, Entry as PlaylistEntry
from .schedule import Schedule

_L = logging.getLogger(__name__)


async def _to_playlists(files: Iterable[Path]) -> AsyncGenerator[Playlist, None]:
    nameless = Playlist()
    for f in files:
        try:
            specs = PlaylistSpec.from_file(f)
            if nameless:
                yield nameless
                nameless = Playlist()
            for spec in specs:
                res = await spec.resolve()
                yield res
        except ValueError:
            nameless.append(PlaylistEntry(resource=f))
    if nameless:
        yield nameless


class _TagType:
    pass


_Tag = _TagType()


class Core:
    """
    Main logic for the software

    This component receives events from and passes them to other components.
    """

    def __init__(self, _: _TagType, files: Iterable[Path], schedule: Path | None):
        self._files = files
        self._sched = schedule
        self._ctx = Ctx([], None)
        # wait for media when playlists are empty
        self._new_plist = asyncio.Event()
        self._rescan_task: asyncio.Task | None = None

    def rescan(self):
        return self._load_ctx()

    def request_rescan(self):
        _L.debug("input file rescan requested")
        if self._rescan_task is None or self._rescan_task.done():
            self._rescan_task = asyncio.create_task(self.rescan())
            _L.debug("scheduled rescan task")

    def medias(self, *, wait: bool) -> AsyncGenerator[Path, None]:
        """
        Return stream of media files

        The stream is autmatically updated when e.g. schedule changes or media files
        are updated.

        :param wait: Whether to wait for media files if none exist
        """

        async def generator() -> AsyncGenerator[Path, None]:
            while True:
                plists = [p for p in self._ctx.active_playlists() if p]
                if not plists:
                    if not wait:
                        return
                    self._new_plist.clear()
                    await self._new_plist.wait()
                    continue
                for plist in plists:
                    for e in plist:
                        yield e.resource
                        await asyncio.sleep(0)
                return

        return generator()

    async def _load_ctx(self):
        _L.debug("(re)loading input file context")
        self._new_plist.set()
        sched = Schedule.from_file(self._sched) if self._sched is not None else None
        playlists = []
        async for p in _to_playlists(self._files):
            playlists.append(p)
        self._ctx = Ctx(playlists, sched)


async def make_core(files: Iterable[Path], schedule: Path | None):
    c = Core(_Tag, files, schedule)
    await c._load_ctx()
    return c
