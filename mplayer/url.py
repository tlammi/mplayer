import glob
import os

from pathlib import Path
from typing import Iterable


def _resolve_abs(scheme: str, path: str):
    if scheme == "file":
        yield Path(path)
    elif scheme == "glob":
        for p in glob.glob(path, recursive=True):
            yield Path(p)
    else:
        raise ValueError(f"Unknown scheme: {scheme}")


def _resolve_rel(root: Path, scheme: str, path: str):
    if scheme == "file":
        yield root / path
    elif scheme == "glob":
        yield from root.rglob(path)
    else:
        raise ValueError(f"Unknown scheme: {scheme}")


def resolve(url: str, *, root: Path | None = None) -> Iterable[Path]:
    """
    Resolve media URLs

    :param url: URL in format <scheme>://<path>. Path can be relative only if root is set
    :param root: Optional root path for the search
    """
    try:
        scheme, path = url.split("://")
    except ValueError:
        scheme, path = "file", url
    if root is None:
        if not os.path.isabs(path):
            raise ValueError("Absolute path required without root")
        yield from _resolve_abs(scheme, path)
    else:
        yield from _resolve_rel(root, scheme, path)
