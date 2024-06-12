"""
Playlist implementation
"""

import asyncio
import os

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, TypeVar, Generic, Dict, Any

import yaml

from . import url
from .filters import Filter, filter_by_name


T = TypeVar("T")


def _filters_from_dict(d: Dict[str, Any]) -> List[Filter]:
    out = []
    for k, v in d.items():
        out.append(filter_by_name(k)(v))
    return out


@dataclass
class Entry(Generic[T]):
    resource: T
    # TODO: Remove
    filters: List[Filter] = field(default_factory=list)


class _PlaylistImpl(Generic[T], List[Entry[T]]):

    def __init__(self, entries: Iterable[Entry[T]] = (), name=""):
        super().__init__(entries)
        self._nm = name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._nm})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self._nm}, entries={[str(e) for e in self]})"

    @property
    def name(self):
        return self._nm


class Playlist(_PlaylistImpl[Path]):
    """
    Playlist containing media files

    This list is not affected by removing files.
    Use PlaylistSpec.resolve() to re-resolve wildcards in those cases
    """

    def __init__(self, entries: Iterable[Entry[Path]] = (), name=""):
        super().__init__(entries, name)


class PlaylistSpec(_PlaylistImpl[str]):
    """
    Playlist specification

    This is typically loaded from a YAML file and can contain wildcards.
    See Playlist for resolved references.
    """

    def __init__(self, entries: Iterable[Entry[str]] = (), name="", root=Path()):
        super().__init__(entries, name)
        self._root = root

    @staticmethod
    def from_yaml(objs: dict | Iterable[dict], root: os.PathLike | None = None):
        root = Path(root) if root is not None else Path()
        if isinstance(objs, dict):
            objs = [objs]
        out = []
        for obj in objs:
            out.append(PlaylistSpec())
            out[-1]._nm = obj.get("name", "")
            for m in obj.get("media", []):
                if isinstance(m, str):
                    out[-1].append(Entry(resource=m))
                else:
                    out[-1].append(
                        Entry(
                            resource=m["url"],
                            filters=_filters_from_dict(m.get("filters", {})),
                        )
                    )
            out[-1]._root = root
        return out

    @staticmethod
    def from_file(path: os.PathLike):
        path = Path(path)
        with open(path) as f:
            return PlaylistSpec.from_yaml(yaml.safe_load_all(f), path.parent)

    async def walk(self):
        """
        Walk the media files without resolving

        This does not store the results anywhere, just walks the wildcard paths
        """
        for e in self:
            res = []
            for f in url.resolve(e.resource, root=self._root):
                await asyncio.sleep(0)
                res.append(f)
            for f in e.filters:
                await asyncio.sleep(0)
                res = f(res)
            for r in res:
                yield r
                await asyncio.sleep(0)

    async def resolve(self) -> Playlist:
        """
        Resolve media paths
        """
        out = Playlist(name=self.name)
        async for e in self.walk():
            out.append(Entry(resource=e))
        return out

    def resolve_sync(self) -> Playlist:
        """
        Resolve media paths
        """
        out = Playlist(name=self.name)
        for e in self:
            res = []
            for f in url.resolve(e.resource, root=self._root):
                assert f.is_absolute()
                res.append(f)
            for f in e.filters:
                res = f(res)
            out.extend(Entry(resource=r) for r in res)
        return out
