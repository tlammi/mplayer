
import tomllib

from pathlib import PurePath
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
        out.path = PurePath(d.get("path", out.path))
        out.socket = PurePath(d.get("socket", out.socket))
        return out


@dataclass
class Config:
    playlist_root: PurePath = PurePath(".")
    playlists: dict[str, list[Suite]] = field(default_factory=dict)
    plai: PlaiConfig | None = None

    @staticmethod
    def from_obj(d: dict) -> "Config":
        out = Config(playlist_root=PurePath(d["playlist-root"]))
        branch_playlists = {}
        playlists = d.get("playlist", {})
        while playlists:
            key, val = playlists.popitem()
            if "from" in val:
                branch_playlists[key] = val["from"]
            else:
                suite = Suite(globs=val["globs"])
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
