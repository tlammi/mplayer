from datetime import datetime
from .schedule import Event, Schedule

class Scheduler:
    def __init__(self, sched: Schedule|None = None):
        self._sched = sched or Schedule()

    def active(self, now = datetime.now()) -> Event | None:
        active: Event|None = None
        for evt in self._sched:
            if evt.at > now:
                return active
            active = evt
        return active
