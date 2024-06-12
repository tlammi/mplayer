"""
Business logic
"""

import logging
import asyncio

from datetime import timedelta, datetime
from typing import Iterable, AsyncGenerator, Dict
from .vlc_player import VlcPlayer
from .schedule import Schedule
from .playlist import PlaylistSpec
from .core import Core

_L = logging.getLogger(__name__)


class App:
    """
    Top level stuff
    """

    def __init__(self, core: Core):
        self._core = core
        self._player = VlcPlayer()
        self._sched_task = None
        self._sched = Schedule()
        self._plists: Dict[str, PlaylistSpec] = {}
        self._repeat = False
        self._plist_name = ""

    async def set_repeat(self, repeat=True):
        self._repeat = repeat

    async def set_image_duration(self, duration: timedelta):
        """
        Set image duration for the player
        """
        await self._player.set_image_duration(duration)

    def set_fullscreen(self, val: bool):
        return self._player.set_fullscreen(val)

    async def play(self):
        while True:
            async for m in self._core.medias(wait=True):
                await self._player.play(m)
            if not self._repeat:
                break
