from datetime import datetime, timedelta

import pytest

from mplayer.schedule import Schedule, RawSchedule, Event, OffsetEvent


def _dt_str(s: str):
    return datetime.fromisoformat(s)

def _td_str(s: str):
    hours, mins, secs = s.split(":")
    return timedelta(hours=int(hours), minutes=int(mins), seconds=int(secs))

def test_default():
    s = Schedule()
    assert len(s) == 0

def test_default_raw():
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

def test_invalid_at():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01 00
"""
    with pytest.raises(ValueError):
        RawSchedule.from_str(data)

def test_offset_to_abs():
    start = _dt_str("2000-01-01")
    prev = Event(playlist="foo", at=start)
    offset = OffsetEvent(playlist="bar", offset=_td_str("10:00:00"))
    res = offset.absolute(prev)
    assert res.playlist=="bar"
    assert res.at == _dt_str("2000-01-01T10:00:00")

def test_sched_abs():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01 00:00:00
[[schedule]]
playlist = "bar"
at = 2000-01-01 00:00:00
"""
    s = Schedule.from_str(data)
    assert len(s) == 2
    foo, bar = s
    assert foo.playlist == "foo"
    assert bar.playlist == "bar"

def test_sched_offset():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01
[[schedule]]
playlist = "bar"
offset = 10:00:00
"""
    s = Schedule.from_str(data)
    _, bar = s
    assert bar.at == _dt_str("2000-01-01T10:00:00")

def test_sched_offset_chained():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01
[[schedule]]
playlist = "bar"
offset = 10:00:00
[[schedule]]
playlist = "baz"
offset = 02:00:00
"""
    s = Schedule.from_str(data)
    _, _, baz = s
    assert baz.at == _dt_str("2000-01-01T12:00:00")

def test_only_time():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01 15:00:00
[[schedule]]
playlist = "bar"
at = 16:00:00
"""
    s = Schedule.from_str(data)
    _, bar = s
    assert bar.playlist == "bar"
    assert bar.at == _dt_str("2000-01-01 16:00:00")


def test_offset_cannot_be_first():
    data = """
[[schedule]]
playlist = "foo"
offset = 10:00:00
"""
    with pytest.raises(ValueError):
        s = RawSchedule.from_str(data)

def test_allow_time_overflow():
    data = """
[[schedule]]
playlist = "foo"
at = "2000-01-01 25:00:00"
"""
    s = Schedule.from_str(data)
    evt = s.pop()
    assert evt.playlist == "foo"
    assert evt.at == _dt_str("2000-01-02 01:00:00")

def test_allow_time_overflow_time_only():
    data = """
[[schedule]]
playlist = "foo"
at = "2000-01-01 00:00:00"
[[schedule]]
playlist = "bar"
at = "25:00:00"
"""
    s = Schedule.from_str(data)
    _, evt = s
    assert evt.playlist == "bar"
    assert evt.at == _dt_str("2000-01-02 01:00:00")

def test_enforce_schedule_order():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01 01:00:00
[[schedule]]
playlist = "bar"
at = 2000-01-01 00:00:00
"""
    with pytest.raises(ValueError):
        Schedule.from_str(data)

