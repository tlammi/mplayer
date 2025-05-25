import asyncio
import logging

from typing import AsyncGenerator
from pathlib import Path, PurePath
from dataclasses import dataclass

from .api.plai import Session as PlaiSession
from . import config, fs, util, wdog

_L = logging.getLogger(__name__)


_EVENT_FILTER = {
     fs.EventType.Modified,
    fs.EventType.Deleted,
    # Created is not needed since writes also emit a Modified event
    # fs.EventType.Created,
    fs.EventType.Moved,
}


async def _monitor_playlist(root: Path, suites: list[config.Suite]) -> AsyncGenerator[fs.Event]:
    generators = [fs.monitor(root, filters=s.globs, events=_EVENT_FILTER) for s in suites]
    async for i in util.multiplex(*generators):
        yield i

def _walk_playlists(root: Path, suites: list[config.Suite]) -> set[Path]:
    _L.debug("Walking playlist directories")
    medias = []
    for s in suites:
        for m in fs.walk(root, filters=s.globs): 
            medias.append(m)
    return set(medias)

# TODO: This should made better. Now this always emits all files, it would be better to separately report
# all files and modified files. Maybe return the whole media set before reset so Player can
# sync files to the frontend more nicely.
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
        await self._wait_plai()
        async with asyncio.TaskGroup() as tg:
            collector: asyncio.Task | None = None
            while True:
                item = await self._queue.get()
                if isinstance(item, Playlist):
                    if collector is not None:
                        collector.cancel()
                    collector = tg.create_task(self._playlist_collector(self._cfg.playlists[item.name]))
                elif isinstance(item, MediaSet):
                    await self._play(item.value)
                else:
                    raise TypeError(f"Unsupported event: {item}")

    async def play(self, playlist: str):
        await self._queue.put(Playlist(playlist))

    async def _playlist_collector(self, playlist: list[config.Suite]):
        async for media_set in _collect_playlist(Path(self._cfg.playlist_root), playlist):
            await self._queue.put(MediaSet(value=media_set))


    async def _wait_plai(self):
        _L.info("Waiting for plai to come up")
        while True:
            async with PlaiSession.unix_session(str(self._cfg.plai.socket)) as sess:
                _L.debug("pinging")
                await sess.ping()
                _L.info("Plai reached")
                return

    async def _play(self, media_set: set[PurePath]):
        media_set = {self._cfg.playlist_root / m for m in media_set}
        media_info = {(fs.sha256(p), p) for p in media_set}
        async with PlaiSession.unix_session(str(self._cfg.plai.socket)) as sess:
            curr_media = await sess.list_medias()
            _L.debug("Medias in frontend: %s", curr_media)
            missing = {m for m in media_info if m[0] not in curr_media}
            _L.debug("Missing from frontend: %s", missing)
            _L.info("Uploading %s medias", len(missing))
            for m in missing:
                await sess.upload_media(m[0], m[1])
            playlist = [m[0] for m in media_info]
            _L.info("Playing playlist")
            _L.debug("Playlist: %s", playlist)
            await sess.play(playlist)

