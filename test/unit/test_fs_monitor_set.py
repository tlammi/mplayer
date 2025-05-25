from pathlib import PurePath

from mplayer import fs


def _path_set(*args: str):
    return {PurePath(a) for a in args}

def _event(src: str, kind: fs.EventType, dst: str|None=None, is_directory=False):
    return fs.Event(
        src=PurePath(src),
        dst=PurePath(dst) if dst else PurePath(),
        kind=kind,
        is_directory=is_directory,
    )


def test_init_empty():
    s = fs.MonitorSet()
    assert len(s.static) == 0
    assert len(s.new) == 0
    assert len(s.modified) == 0
    assert len(s.removed) == 0

def test_init_val():
    val = _path_set("foo", "bar")
    s = fs.MonitorSet(val)
    assert s.static == val
    assert len(s.new) == 0
    assert len(s.modified) == 0
    assert len(s.removed) == 0

def test_add_new():
    s = fs.MonitorSet()
    s.add(_event("foo", fs.EventType.Created))
    assert s.static == set()
    assert s.new == _path_set("foo")
    s.reset()
    assert s.static == _path_set("foo")
    assert s.new == set()

def test_add_remove():
    val = _path_set("foo")
    s = fs.MonitorSet(val)
    s.add(_event("foo", fs.EventType.Deleted))
    assert s.static == val
    assert s.removed == _path_set("foo")
    s.reset()
    assert s.static == set()
    assert s.removed == set()

def test_add_modfied():
    val = _path_set("foo")
    s = fs.MonitorSet(val)
    s.add(_event("foo", fs.EventType.Modified))
    assert s.static == val
    assert s.modified == _path_set("foo")
    s.reset()
    assert s.static == _path_set("foo")
    assert s.modified == set()
