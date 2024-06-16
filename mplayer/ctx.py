"""
Context
"""

import asyncio
import logging

from datetime import datetime
from pathlib import Path
from collections.abc import AsyncGenerator, Collection, Iterable

from .playlist import Playlist
from .schedule import Schedule

_L = logging.getLogger(__name__)


class Ctx:
    """
    Holds playlists and schedule and emits medias based on those

    This does not know anything about rescanning
    """

    def __init__(self, playlists: Iterable[Playlist], schedule: Schedule | None = None):
        self._sched = schedule
        self._plists = {p.name: p for p in playlists}
        self._active_plist = None
        if self._sched is not None:
            curr = self._sched.current()
            if curr is not None:
                self._active_plist = curr.playlist
        if self._sched is not None:
            self._update_task = asyncio.create_task(self._update_active_playlist())

    def valid(self) -> bool:
        """
        Check if the context is valid, i.e. schedule points to valid playlists
        """
        if self._sched is None:
            return True
        for e in self._sched:
            if e.playlist not in self._plists:
                return False
        return True

    def active_playlists(self) -> Collection[Playlist]:
        """
        Return the currently active playlists

        If a schedule is active this returns a collection with size 1.
        If no schedule is active this returns all the playlists in the current object.
        """
        if self._active_plist is not None:
            return [self._plists[self._active_plist]]
        return self._plists.values()

    async def _update_active_playlist(self):
        assert self._sched is not None
        _L.debug("scheduling enabled")
        while True:
            try:
                self._active_plist = await self._next_event(self._sched)
                _L.info('switched active playlist to "%s"', self._active_plist)
            except asyncio.CancelledError:
                _L.info("no more events in schedule")
                break

    @staticmethod
    async def _next_event(sched: Schedule) -> str:
        next_event = sched.next()
        if next_event is None:
            raise asyncio.CancelledError()
        diff = next_event.when - datetime.now()
        _L.debug("next event in schedule in %ss", diff.total_seconds())
        await asyncio.sleep((next_event.when - datetime.now()).total_seconds())
        return next_event.playlist
