
import logging
import argparse
import asyncio

from pathlib import Path

import httpx

from .config import Config
from .schedule import Schedule
from .scheduler import Scheduler
from . import fs
from .api.plai import Session as PlaiSession

_L = logging.getLogger(__name__)

async def once(cfg: Config, sched: Schedule, sock: str):
    """
    Script for walking directory hierarchy based on config and populating Plai with the files
    """
    curr = Scheduler(sched).active()
    if curr is None:
        _L.info("No active event in schedule. Doing nothing")
        return
    playlist = cfg.playlists[curr.playlist]
    globs = [g for l in playlist for g in l.globs]
    _L.debug("globs: '%s'", globs)
    root = Path(cfg.playlist_root)
    medias = [root/m for m in fs.walk(root, filters=globs)]
    media_info = {(fs.sha256(p), p) for p in medias}
    async with PlaiSession.unix_session(sock) as sess:
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


def once_cli(ns: argparse.Namespace):
    return once(Config.from_file(ns.config), Schedule.from_file(ns.schedule), ns.sock)
