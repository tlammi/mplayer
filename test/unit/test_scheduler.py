import pytest

from datetime import datetime, timedelta

from mplayer.scheduler import Scheduler
from mplayer.schedule import Schedule, Event


def _mk_dt(hours: int=0, minutes: int=0, seconds: int=0):
    dt = datetime.fromisoformat("2025-04-13")
    return dt + timedelta(hours, minutes, seconds)

async_ = pytest.mark.asyncio


def test_init_default():
    s = Scheduler()
    assert s.active() is None

def test_active_event():
    sched = Schedule()
    sched.append(Event(playlist="foo", at=_mk_dt(-1)))
    s = Scheduler(sched)
    evt = s.active()
    assert evt is not None

def test_future_event():
    sched=Schedule([Event(playlist="foo", at=_mk_dt(1))])
    evt = Scheduler(sched).active(_mk_dt())
    assert evt is None

def test_events_multiple():
    sched = Schedule([Event(playlist="foo", at=_mk_dt(-1)), Event(playlist="bar", at=_mk_dt(minutes=1)), Event(playlist="baz", at=_mk_dt(1))])
    s = Scheduler(sched)
    evt = s.active(_mk_dt(-2))
    assert evt is None
    evt = s.active(_mk_dt())
    assert evt is not None
    assert evt.playlist == "foo"
    evt = s.active(_mk_dt(minutes=10))
    assert evt is not None
    assert evt.playlist == "bar"
    evt = s.active(_mk_dt(2))
    assert evt is not None
    assert evt.playlist == "baz"

