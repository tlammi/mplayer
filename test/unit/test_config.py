from pathlib import PurePath

from mplayer.config import Config, Suite

def test_init_default():
    Config()

def test_empty():
    data = """
root = "."
"""
    c = Config.from_str(data)
    assert c.root == PurePath(".")
    assert len(c.playlists) == 0

def test_playlist():
    data = """
root = "."

[playlist.foo]
globs = ["asdf"]
"""
    c = Config.from_str(data)
    assert len(c.playlists) == 1
    suite = c.playlists["foo"]
    assert len(suite) == 1
    v = suite.pop()
    assert v.globs == ["asdf"]

def test_ref_playlist():
    data = """
root = "."
[playlist.foo]
from = ["bar"]
[playlist.bar]
globs = ["asdf"]
"""
    c = Config.from_str(data)
    assert len(c.playlists) == 2
    foo = c.playlists["foo"]
    assert len(foo) == 1
    suite = foo.pop()
    assert suite.globs == ["asdf"]

def test_ref_2_playlist():
    data = """
root = "."
[playlist.foo]
from = ["bar", "baz"]
[playlist.bar]
globs = ["asdf"]
[playlist.baz]
globs = ["fdsa"]
"""
    c = Config.from_str(data)
    assert len(c.playlists) == 3
    foo = c.playlists["foo"]
    assert len(foo) == 2
    bar, baz = foo
    assert bar.globs == ["asdf"]
    assert baz.globs == ["fdsa"]

