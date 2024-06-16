"""
Scheduling
"""

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Iterable
import yaml


@dataclass
class Event:
    when: datetime
    playlist: str

    def __hash__(self):
        return hash((self.when, self.playlist))


class Schedule(List[Event]):
    """
    Contains instructions on changing behavior

    """

    def __init__(self, events: Iterable[Event] | None = None):
        events = events or []
        events = sorted(events, key=lambda e: e.when)
        super().__init__(events)

    @staticmethod
    def from_yaml(objs: list, now=datetime.now()):
        events = []
        for obj in objs:
            a = obj["after"]
            if isinstance(a, str):
                if a.startswith("now+"):
                    a = a[4:]
                    a = now + timedelta(seconds=int(a))
                else:
                    a = datetime.strptime(a, "%Y-%m-%d %H:%M")
            elif isinstance(a, int):
                a = datetime.fromtimestamp(a)
            else:
                raise ValueError(f"Unsupported time format: {a}")
            events.append(Event(when=a, playlist=obj["playlist"]))
        return Schedule(events)

    @staticmethod
    def from_file(path: os.PathLike):
        with open(path) as f:
            return Schedule.from_yaml(yaml.safe_load(f))

    def current(self, now=datetime.now()) -> Event | None:
        """
        Get the currently active event
        """
        for e in reversed(self):
            if e.when <= now:
                return e
        return None

    def next(self, now: datetime | None = None) -> Event | None:
        """
        Get the next event
        """
        now = now or datetime.now()
        for e in self:
            if e.when > now:
                print(e.when, now)
                return e
        return None

    def non_expired(self, now=datetime.now()) -> "Schedule":
        for i, e in enumerate(reversed(self)):
            if e.when <= now:
                return Schedule(self[len(self) - 1 - i :])
        return Schedule()
