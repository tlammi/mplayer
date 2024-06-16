import os
import asyncio
import logging

from datetime import timedelta

import vlc

from .player import Player
from .persist import persist

_L = logging.getLogger(__name__)


class VlcPlayer(Player):

    def __init__(self):
        # args = ["--no-xlib"]
        args = []
        if _L.level != "DEBUG":
            args.append("--quiet")
        self._inst = vlc.Instance(*args)
        self._player = self._inst.media_player_new()
        self._loop = asyncio.get_running_loop()
        self._player.event_manager().event_attach(
            vlc.EventType.MediaPlayerEndReached, lambda _: self._play_done()
        )
        self._sem = asyncio.Semaphore(0)
        self._img_dur = None

    async def set_image_duration(self, duration: timedelta):
        _L.debug("image duration set: %s", self._img_dur)
        self._img_dur = duration

    async def set_fullscreen(self, val: bool):
        self._player.set_fullscreen(val)

    async def play(self, file: os.PathLike):
        # Open so the file is not deleted by accident
        with persist(file) as tmp:
            _L.debug("playing %s", tmp.name)
            media = self._inst.media_new(tmp)
            if self._img_dur is not None:
                media.add_option(f"image-duration={self._img_dur.total_seconds()}")

            # This would be nice info but parsing takes like 0.2 sec on my laptop
            # so not worth it
            # media.parse()
            # _L.debug("media duration: %ss", media.get_duration() / 1000)
            self._player.set_media(media)
            self._player.play()
            try:
                await self._sem.acquire()
            except asyncio.CancelledError:
                self._player.stop()
                raise

    def _play_done(self):
        self._loop.call_soon_threadsafe(self._sem.release)
