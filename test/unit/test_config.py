from pathlib import PurePath

from mplayer.config import Config, RawConfig, Playlist, RefPlaylist

def test_init_default():
    RawConfig()
    Config()

def test_raw_empty():
    data = """
root = "."
"""
    c = RawConfig.from_str(data)
    assert c.root == PurePath(".")
    assert len(c.playlists) == 0

def test_raw_playlist():
    data = """
root = "."

[playlist.foo]
globs = ["asdf"]
"""
    c = RawConfig.from_str(data)
    assert len(c.playlists) == 1
    v = c.playlists["foo"]
    assert isinstance(v, Playlist)
    assert v.globs == ["asdf"]

def test_raw_ref_playlist():
    data = """
root = "."
[playlist.foo]
from = ["bar"]
[playlist.bar]
globs = ["asdf"]
"""
    c = RawConfig.from_str(data)
    assert len(c.playlists) == 2
    foo = c.playlists["foo"]
    assert isinstance(foo, RefPlaylist)
    assert foo.from_ == ["bar"]
