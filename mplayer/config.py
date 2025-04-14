
import tomllib

from pathlib import PurePath
from dataclasses import dataclass, field

import dacite


@dataclass
class FilterNewest:
    count: int

Filter = None | FilterNewest

_FILTER_MAP = {
    "newest": FilterNewest
}

@dataclass
class Suite:
    globs: list[str] = field(default_factory=list)
    filter: Filter = None

@dataclass
class Config:
    root: PurePath = PurePath(".")
    playlists: dict[str, list[Suite]] = field(default_factory=dict)

    @staticmethod
    def from_obj(d: dict) -> "Config":
        out = Config(root=PurePath(d["root"]))
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
                    algo = filt.pop("algo")
                    suite.filter = dacite.from_dict(_FILTER_MAP[algo], filt)
                out.playlists[key] = [suite]

        for key, children in branch_playlists.items():
            out.playlists[key] = [p for c in children for p in out.playlists[c]]
        return out

    @classmethod
    def from_str(cls, s: str) -> "Config":
        return cls.from_obj(tomllib.loads(s))
