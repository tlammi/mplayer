
import tomllib

from pathlib import PurePath
from dataclasses import dataclass, field


@dataclass
class FilterNewest:
    count: int

Filter = None | FilterNewest

@dataclass
class Playlist:
    globs: list[str] = field(default_factory=list)
    filter: Filter = None

@dataclass
class RefPlaylist:
    from_: list[Playlist]

@dataclass
class RawConfig:
    root: PurePath = PurePath(".")
    playlists: dict[str, Playlist|RefPlaylist] = field(default_factory=dict)

    @staticmethod
    def from_obj(d: dict) -> "RawConfig":
        out = RawConfig(root=PurePath(d["root"]))
        for key, val in d.get("playlist", {}).items():
            if "from" in val:
                out.playlists[key] = RefPlaylist(from_ = val["from"])
            else:
                out.playlists[key] = Playlist(globs=val["globs"])
        return out

    @classmethod
    def from_str(cls, s: str) -> "RawConfig":
        return cls.from_obj(tomllib.loads(s))


class Config:
    root: PurePath = PurePath(".")
    playlists: dict[str, Playlist] = field(default_factory=dict)
