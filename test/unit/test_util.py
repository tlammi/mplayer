from datetime import timedelta, time

from mplayer import util


def _tm_str(s: str) -> time:
    return time.fromisoformat(s)

def test_parse_timedelta():
    assert util.parse_timedelta("1s") == timedelta(seconds=1)
    assert util.parse_timedelta("1m") == timedelta(minutes=1)
    assert util.parse_timedelta("1h") == timedelta(hours=1)
    assert util.parse_timedelta("1d") == timedelta(days=1)


def test_overflow_zero():
    tm, days = util.parse_time_overflow("00:00:00")
    assert tm == _tm_str("00:00:00")
    assert days == 0
