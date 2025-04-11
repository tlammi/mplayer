from datetime import datetime

from mplayer.schedule_doc import ScheduleDoc


def _dt_str(s: str):
    return datetime.fromisoformat(s)


def test_default():
    s = ScheduleDoc()
    assert len(s) == 0

def test_from_str_empty():
    s = ScheduleDoc.from_str("")
    assert len(s) == 0

def test_from_str_enums_only():
    s = ScheduleDoc.from_str('playlists = ["foo", "bar"]')
    assert len(s) == 0

def test_from_str_one():
    data = """
[[schedule]]
playlist = "foo"
at = 2000-01-01
"""
    s = ScheduleDoc.from_str(data)
    assert len(s) == 1
    evt = s[0]
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
    s = ScheduleDoc.from_str(data)
    assert len(s) == 2
    foo, bar = s
    assert foo.playlist == "foo"
    assert bar.playlist == "bar"
    assert foo.at == _dt_str("2000-01-01T00:00:00")
    assert bar.at == _dt_str("2000-01-01T01:00:00")

