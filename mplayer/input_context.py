"""
Wrapper for centralized input file reloading
"""

import logging
import asyncio

from pathlib import Path
from typing import Dict, List, Tuple, Callable, Set
from datetime import datetime
from dataclasses import dataclass, field

from .playlist import PlaylistSpec, Playlist, Entry as PlaylistEntry
from .schedule import Schedule

_L = logging.getLogger()


@dataclass
class _Ctx:
    """
    Group all member variables together for easier rescan

    Rescan has to be done separately and the state has to be updated in one operation
    so the media show does not behave strangely.
    """

    clock: Callable[[], datetime]
    last_scan: float
    media_files: Set[Path] = field(default_factory=set)
    playlist_files: Set[Path] = field(default_factory=set)
    sched_file: Path | None = None
    playlists: Dict[str, Playlist] = field(default_factory=dict)
    schedule: Schedule | None = None

    def copy(self) -> "_Ctx":
        return _Ctx(
            clock=self.clock,
            last_scan=self.last_scan,
            media_files=self.media_files.copy(),
            playlist_files=self.playlist_files.copy(),
            sched_file=self.sched_file,
            playlists=self.playlists.copy(),
            schedule=Schedule(self.schedule.copy()) if self.schedule else None,
        )

    def schedule_valid(self) -> bool:
        """
        Check if all the items in schedule reference valid playlists
        """
        if not self.schedule:
            return True
        for elem in self.schedule:
            if elem.playlist not in self.playlists.keys():
                return False
        return True

    def discard_removed_media_files(self):
        removed_files = []
        media_files = set()
        for m in self.media_files:
            if m.is_file():
                media_files.add(m)
            else:
                removed_files.append(m)
        _L.info('Medias removed: "%s"', removed_files)
        self.media_files = media_files
        for r in removed_files:
            for p in self.playlists.values():
                if r in p:
                    p.remove(r)
        return removed_files


class InputContext:
    """
    Centralized input file management

    Manages input files and allows e.g. to centrally reload everything
    """

    def __init__(self, *files: Path, schedule: None | Path, clock=datetime.now):
        self._assert_paths(schedule, *files)
        if schedule:
            assert schedule.is_absolute()
            assert schedule.is_file()
        for f in files:
            assert f.is_absolute()
            assert f.is_file()
        sched_file, sched = self._load_schedule(schedule)
        ctx = _Ctx(
            clock=clock,
            last_scan=clock().timestamp(),
            sched_file=sched_file,
            schedule=sched,
        )
        playlists_and_specs: List[PlaylistSpec | Playlist] = []
        for f in files:
            try:
                playlists_and_specs.extend(PlaylistSpec.from_file(f))
                ctx.playlist_files.add(f)
            except ValueError:
                if not playlists_and_specs or isinstance(
                    playlists_and_specs[-1], PlaylistSpec
                ):
                    playlists_and_specs.append(Playlist())
                assert isinstance(playlists_and_specs[-1], Playlist)
                playlists_and_specs[-1].append(PlaylistEntry(f))
                ctx.media_files.add(f)

        def convert(p: Playlist | PlaylistSpec) -> Playlist:
            if isinstance(p, PlaylistSpec):
                return p.resolve_sync()
            return p

        ctx.playlists = {p.name: convert(p) for p in playlists_and_specs}
        for p in ctx.playlists.values():
            for e in p:
                ctx.media_files.add(e.resource)
        self._ctx = ctx

    @property
    def schedule(self) -> Schedule | None:
        return self._ctx.schedule

    @property
    def playlists(self) -> Dict[str, Playlist]:
        return self._ctx.playlists

    async def rescan(self) -> bool:
        """
        Rescan the input files

        :return True if something changed
        """
        ctx = self._ctx.copy()
        changed = False
        now = ctx.clock().timestamp()
        if ctx.sched_file is not None:
            if ctx.sched_file.stat().st_mtime > ctx.last_scan:
                _L.info("schedule updated")
                try:
                    _, sched = self._load_schedule(ctx.sched_file)
                    ctx.schedule = sched
                    changed = True
                except FileNotFoundError:
                    _L.error(
                        'Schedule file "%s" not found. Continuing with the current schedule',
                        ctx.sched_file,
                    )
        for p in ctx.playlist_files:
            if p.stat().st_mtime > ctx.last_scan:
                _L.warning('Playlist "%s" changed. Reload not implemented yet', p)
            await asyncio.sleep(0)

        discarded = ctx.discard_removed_media_files()
        if discarded:
            changed = True
        for path in ctx.playlist_files:
            specs = PlaylistSpec.from_file(path)
            for spec in specs:
                playlist = await spec.resolve()
                orig_len = len(ctx.media_files)
                ctx.media_files.update(e.resource for e in playlist)
                if len(ctx.media_files) != orig_len:
                    _L.info('New media files added to playlist "%s"', playlist.name)
                    changed = True
        ctx.last_scan = now
        self._ctx = ctx
        return changed

    @staticmethod
    def _load_schedule(sched: Path | None) -> Tuple[None, None] | Tuple[Path, Schedule]:
        if sched is None:
            return None, None
        return (sched, Schedule.from_file(sched))

    @staticmethod
    def _assert_paths(*files: Path | None):
        for f in files:
            if f is None:
                continue
            assert f.is_absolute()
            assert f.is_file()
