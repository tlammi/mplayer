from datetime import datetime, timedelta

import yaml

from mplayer.schedule import Schedule, Event


def _mk_datetime(stamp: int):
    return datetime.fromtimestamp(stamp)


def _mk_event(stamp: int):
    return Event(when=_mk_datetime(stamp), playlist=str(stamp))


def test_init():
    s = Schedule()
    assert len(s) == 0


def test_init_event():
    s = Schedule({Event(when=datetime.now(), playlist="a")})
    assert len(s) == 1


def test_init_event_list():
    s = Schedule(
        [
            Event(when=_mk_datetime(1), playlist="a"),
            Event(when=_mk_datetime(0), playlist="b"),
        ]
    )
    assert len(s) == 2
    assert s == [
        Event(when=_mk_datetime(0), playlist="b"),
        Event(when=_mk_datetime(1), playlist="a"),
    ]


def test_current():
    s = Schedule([_mk_event(1), _mk_event(0), _mk_event(3)])
    e = s.current(now=_mk_datetime(2))
    assert e == _mk_event(1)


def test_next():
    s = Schedule([_mk_event(1), _mk_event(0), _mk_event(3)])
    e = s.next(now=_mk_datetime(2))
    assert e == _mk_event(3)


def test_non_expired():
    s = Schedule([_mk_event(1), _mk_event(0), _mk_event(3)])
    s = s.non_expired(now=_mk_datetime(2))
    assert s == [_mk_event(1), _mk_event(3)]


def test_parse():
    yml = """
- after: 0
  playlist: "asdf"
"""
    s = Schedule.from_yaml(yaml.safe_load(yml))
    assert s == Schedule([Event(when=datetime.fromtimestamp(0), playlist="asdf")])


def test_parse_delta():
    yml = """
- after: now+1
  playlist: "asdf"
"""
    now = datetime.now()
    plus_one = now + timedelta(seconds=1)
    s = Schedule.from_yaml(yaml.safe_load(yml), now)
    assert s == Schedule([Event(when=plus_one, playlist="asdf")])


def test_parse_abs():
    now = datetime.now().replace(second=0, microsecond=0)
    now_txt = now.strftime("%Y-%m-%d %H:%M")
    yml = f"""
- after: {now_txt}
  playlist: "asdf"
"""
    s = Schedule.from_yaml(yaml.safe_load(yml), now)
    assert s == Schedule([Event(when=now, playlist="asdf")])
