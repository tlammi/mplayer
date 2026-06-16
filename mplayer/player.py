import asyncio
import logging

from typing import AsyncGenerator
from pathlib import Path, PurePath
from dataclasses import dataclass

import httpx

from .api.plai import Session as PlaiSession
from . import config, fs, wdog

_L = logging.getLogger(__name__)

_EVENT_MASK = {
    fs.EventType.Created,
    fs.EventType.Modified,
    fs.EventType.Moved,
    fs.EventType.Deleted,
}

async def _monitor_task(wd: wdog.Wdog, root: Path, suite: config.Suite, out: fs.MonitorSet):
    async for i in fs.monitor(root, filters=suite.globs, events=_EVENT_MASK):
        out.add(i)
        await wd.kick()

def _walk_playlist(root: Path, suite: config.Suite) -> fs.MonitorSet:
    _L.info("Walking playlist directories")
    medias = []
    _L.debug("Globs: '%s'", suite.globs)
    suite_medias = [root/m for m in fs.walk(root, filters=suite.globs)]
    selector = fs.make_selector(suite.filters)
    medias.extend(selector.select(suite_medias))
    return fs.MonitorSet(set(medias))

# TODO: This should made better. Now this always emits all files, it would be better to separately report
# all files and modified files. Maybe return the whole media set before reset so Player can
# sync files to the frontend more nicely.
async def _collect_playlist(root: Path, suites: list[config.Suite]) -> AsyncGenerator[set[Path], None]:
    media_sets = [_walk_playlist(root, s) for s in suites]
    yield set().union(*[s.static for s in media_sets])

    wd = wdog.Wdog(10.0, initial_block=True)

    async with asyncio.TaskGroup() as tg:
        for s, ms in zip(suites, media_sets):
            tg.create_task(_monitor_task(wd, root, s, ms))
        while True:
            await wd.run()
            for s, ms in zip(suites, media_sets):
                ms.reset()
                ms.filter_static(s.filters)
            yield set().union(*[ms.static for ms in media_sets])


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
            try:
                async with PlaiSession.unix_session(str(self._cfg.plai.socket)) as sess:
                    _L.debug("pinging")
                    await sess.ping()
                    _L.info("Plai reached")
                    return
            except httpx.ConnectError:
                await asyncio.sleep(1)

    async def _play(self, media_set: set[PurePath]):
        media_set = {self._cfg.playlist_root / m for m in media_set}
        media_info = {(fs.sha256(p), p) for p in media_set}
        async with PlaiSession.unix_session(str(self._cfg.plai.socket)) as sess:
            curr_media = await sess.list_medias()
            # Only patch if the playlist is not empty
            do_patch = bool(curr_media)
            _L.debug("Medias in frontend: %s", curr_media)
            missing = {m for m in media_info if m[0] not in curr_media}
            _L.debug("Missing from frontend: %s", missing)
            _L.info("Uploading %s medias", len(missing))
            for m in missing:
                await sess.upload_media(m[0], m[1])
            playlist = [m[0] for m in media_info]
            _L.info("Playing playlist")
            _L.debug("Playlist: %s", playlist)
            if do_patch:
                _L.info("Playlist not empty, patching the playlist")
                await sess.amend_play(playlist)
            else:
                _L.info("Empty playlist, posting")
                await sess.play(playlist)
                self._first_play = False

