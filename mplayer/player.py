import asyncio
import logging

from typing import AsyncGenerator
from pathlib import Path, PurePath
from dataclasses import dataclass

from .api.plai import Session as PlaiSession
from . import config, fs, util, wdog

_L = logging.getLogger(__name__)


async def _monitor_playlist(root: Path, suites: list[config.Suite]) -> AsyncGenerator[fs.Event]:
    generators = [fs.monitor(root, filters=s.globs) for s in suites]
    async for i in util.multiplex(*generators):
        yield i

def _walk_playlists(root: Path, suites: list[config.Suite]) -> set[Path]:
    _L.debug("Walking playlist directories")
    medias = []
    for s in suites:
        for m in fs.walk(root, filters=s.globs): 
            medias.append(m)
    return set(medias)

async def _collect_playlist(root: Path, suites: list[config.Suite]) -> AsyncGenerator[set[PurePath]]:
    initial = _walk_playlists(root, suites)
    media_set = fs.MonitorSet(initial) #type: ignore
    yield media_set.static

    wd = wdog.Wdog(10.0, initial_block=True)

    async def subtask():
        async for item in _monitor_playlist(root, suites):
            media_set.add(item)
            await wd.kick()

    async with asyncio.TaskGroup() as tg:
        tg.create_task(subtask())
        while True:
            await wd.run()
            media_set.reset()
            yield media_set.static

@dataclass
class Playlist:
    name: str

@dataclass
class MediaSet:
    value: set[PurePath]

class Player:
    def __init__(self, cfg: config.Config):
        _L.debug("Initializing Player")
        self._cfg = cfg
        self._playlist: str = ""
        self._queue = asyncio.Queue()

    async def run(self):
        async with asyncio.TaskGroup() as tg:
            collector: asyncio.Task | None = None
            while True:
                item = await self._queue.get()
                if isinstance(item, Playlist):
                    if collector is not None:
                        collector.cancel()
                    collector = tg.create_task(self._playlist_collector(self._cfg.playlists[item.name]))
                elif isinstance(item, MediaSet):
                    # TODO: Pass to plai API
                    print(f"media_set: {item.value}")
                else:
                    raise TypeError(f"Unsupported event: {item}")

    async def play(self, playlist: str):
        await self._queue.put(Playlist(playlist))


    async def _playlist_collector(self, playlist: list[config.Suite]):
        async for media_set in _collect_playlist(Path(self._cfg.playlist_root), playlist):
            await self._queue.put(MediaSet(value=media_set))
