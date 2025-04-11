
from dataclasses import dataclass
from datetime import datetime, date, timedelta, time

import tomli


def _to_datetime(val: datetime | date):
    if isinstance(val, datetime):
        return val
    return datetime.combine(val, datetime.min.time())

def _to_timedelta(val: timedelta | time):
    if isinstance(val, timedelta):
        return val
    return timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)

@dataclass
class Event:
    playlist: str
    at: datetime

    @staticmethod
    def from_obj(d: dict)->"Event":
        try:
            return Event(d["playlist"], _to_datetime(d["at"]))
        except KeyError:
            raise ValueError("Invalid event")

@dataclass
class OffsetEvent:
    playlist: str
    offset: timedelta

    @staticmethod
    def from_obj(d: dict) -> "OffsetEvent":
        return OffsetEvent(playlist=d["playlist"], offset=_to_timedelta(d["offset"]))


class ScheduleDoc(list):
    def __init__(self):
        pass

    @staticmethod
    def from_obj(data: dict) -> "ScheduleDoc":
        s = ScheduleDoc()
        for obj in data.get("schedule", []):
            try:
                s.append(Event.from_obj(obj))
            except ValueError:
                s.append(OffsetEvent.from_obj(obj))
        return s

    @classmethod
    def from_str(cls, data: str):
        return cls.from_obj(tomli.loads(data))

