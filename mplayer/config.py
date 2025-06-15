
import tomllib

from pathlib import PurePath, Path
from dataclasses import dataclass, field
from datetime import timedelta, time

import dacite

@dataclass
class FilterNewest:
    count: int

@dataclass
class FilterNewerThan:
    max_age: timedelta

Filter = FilterNewest | FilterNewerThan

_FILTER_MAP = {
    "newest": FilterNewest,
    "newer_than": FilterNewerThan,
}

def _time_to_timedelta(t: time) -> timedelta:
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)

_FILTER_CONF_CONVERT_MAP = {
    "max_age": _time_to_timedelta
}

def _convert_filter_conf(d: dict):
    for k, v in _FILTER_CONF_CONVERT_MAP.items():
        if k in d.keys():
            d[k] = v(d[k])
    return d


@dataclass
class Suite:
    globs: list[str] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)

@dataclass
class PlaiConfig:
    run: bool = False
    path: PurePath = PurePath("plai")
    socket: PurePath = PurePath("/tmp/plai.sock")

    @staticmethod
    def from_obj(d: dict) -> "PlaiConfig":
        out = PlaiConfig()
        out.run = d.get("run", out.run)
        out.path = Path(d.get("path", out.path)).expanduser()
        out.socket = Path(d.get("socket", out.socket)).expanduser()
        return out

    def resolve_paths(self, config_path: PurePath):
        path = config_path.parent
        if not self.path.is_absolute() and "/" in self.path.as_posix():
            self.path = path / self.path
        if not self.socket.is_absolute() and "/" in self.socket.as_posix():
            self.socket = path / self.socket


@dataclass
class Config:
    playlist_root: PurePath = PurePath(".")
    playlists: dict[str, list[Suite]] = field(default_factory=dict)
    plai: PlaiConfig = field(default_factory=PlaiConfig)

    @staticmethod
    def from_obj(d: dict) -> "Config":
        playlist_root = Path(d["playlist-root"])
        playlist_root.expanduser()
        out = Config(playlist_root=playlist_root.expanduser())
        branch_playlists = {}
        playlists = d.get("playlist", {})
        while playlists:
            key, val = playlists.popitem()
            if "from" in val:
                branch_playlists[key] = val["from"]
            else:
                globs = val["globs"]
                if isinstance(globs, str):
                    globs = [globs]
                suite = Suite(globs=globs)
                filt = val.get("filter")
                if filt:
                    filt = _convert_filter_conf(filt)
                    algos = [s.strip() for s in filt.pop("algo").split("|")]
                    suite.filters = [dacite.from_dict(_FILTER_MAP[a], filt) for a in algos]
                out.playlists[key] = [suite]

        for key, children in branch_playlists.items():
            out.playlists[key] = [p for c in children for p in out.playlists[c]]
        
        out.plai = PlaiConfig.from_obj(d.get("plai", {}))

        return out

    @classmethod
    def from_str(cls, s: str) -> "Config":
        return cls.from_obj(tomllib.loads(s))

    @classmethod
    def from_file(cls, p: PurePath) -> "Config":
        with open(p) as f:
            return cls.from_str(f.read())

    def resolve_paths(self, config_path: PurePath):
        path = config_path.parent
        if not self.playlist_root.is_absolute():
            self.playlist_root = path / self.playlist_root
        self.plai.resolve_paths(config_path)

