from datetime import datetime, timedelta

import pytest

from mplayer.schedule import RawSchedule, Event, OffsetEvent


def _dt_str(s: str):
    return datetime.fromisoformat(s)

def _td_str(s: str):
    hours, mins, secs = s.split(":")
    return timedelta(hours=int(hours), minutes=int(mins), seconds=int(secs))

def test_default():
    s = RawSchedule()
    assert len(s) == 0

def test_from_str_empty():
    s = RawSchedule.from_str("")
    assert len(s) == 0

def test_from_str_enums_only():
    s = RawSchedule.from_str('playlists = ["foo", "bar"]')
    assert len(s) == 0

def test_from_str_one():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01
"""
    s = RawSchedule.from_str(data)
    assert len(s) == 1
    evt = s[0]
    assert isinstance(evt, Event)
    assert evt.playlist == "foo"
    assert evt.at == _dt_str("2000-01-01")

def test_from_str_two():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01 00:00:00

[[schedule]]
playlist = "bar"
at = 2000-01-01 01:00:00
"""
    s = RawSchedule.from_str(data)
    assert len(s) == 2
    foo, bar = s
    assert isinstance(foo, Event)
    assert isinstance(bar, Event)
    assert foo.playlist == "foo"
    assert bar.playlist == "bar"
    assert foo.at == _dt_str("2000-01-01T00:00:00")
    assert bar.at == _dt_str("2000-01-01T01:00:00")

def test_offset_event():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01
[[schedule]]
playlist = "bar"
offset = 01:00:00
"""
    s = RawSchedule.from_str(data)
    assert len(s) == 2
    foo, bar = s
    assert foo.playlist == "foo"
    assert bar.playlist == "bar"
    assert isinstance(bar, OffsetEvent)
    assert bar.offset == _td_str("01:00:00")

def test_invalid_enum():
    data = """
playlists = ["foo", "bar"]
[[schedule]]
playlist = "baz"
at = 2000-01-01 00:00:00
"""
    with pytest.raises(ValueError):
        RawSchedule.from_str(data)
