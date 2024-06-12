from datetime import timedelta

from mplayer import util


def test_parse_timedelta():
    assert util.parse_timedelta("1s") == timedelta(seconds=1)
    assert util.parse_timedelta("1m") == timedelta(minutes=1)
    assert util.parse_timedelta("1h") == timedelta(hours=1)
    assert util.parse_timedelta("1d") == timedelta(days=1)
