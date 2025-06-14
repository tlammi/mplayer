import asyncio
from datetime import datetime
from typing import AsyncGenerator, Callable
from .schedule import Event, Schedule

async def _sleep_until(now: datetime, until: datetime):
    delay = (until - now).total_seconds()
    if delay > 0:
        await asyncio.sleep(delay)

class Scheduler:
    def __init__(self, sched: Schedule|None = None):
        self._sched = sched or Schedule()

    def active(self, now = datetime.now()) -> Event | None:
        idx = self._active_idx(now)
        if idx < 0:
            return None
        return self._sched[idx]

    def next(self, now = datetime.now()) -> Event | None:
        idx = self._active_idx(now)+1
        if idx >= len(self._sched):
            return None
        return self._sched[idx]

    async def event_stream(self, clock: Callable[[], datetime] = datetime.now) -> AsyncGenerator[Event, None]:
        idx = self._active_idx(clock())
        sched = self._sched
        if idx >= 0:
            yield self._sched[idx]
            sched = sched[idx+1:]
        while sched:
            evt = sched.pop(0)
            await _sleep_until(clock(), evt.at)
            yield evt

    def _active_idx(self, now: datetime) -> int:
        active = -1
        for idx, evt in enumerate(self._sched):
            if evt.at > now:
                return active
            active = idx
        return active

