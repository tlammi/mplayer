
from dataclasses import dataclass
from datetime import datetime, date, timedelta

import tomli


def _to_datetime(val: datetime | date):
    if isinstance(val, datetime):
        return val
    return datetime.combine(val, datetime.min.time())

@dataclass
class Event:
    playlist: str
    at: datetime

@dataclass
class OffsetEvent:
    playlist: str
    offset: timedelta


class ScheduleDoc(list):
    def __init__(self):
        pass

    @staticmethod
    def from_obj(data: dict) -> "ScheduleDoc":
        s = ScheduleDoc()
        for obj in data.get("schedule", []):
            s.append(Event(playlist=obj["playlist"], at=_to_datetime(obj["at"])))
        return s

    @classmethod
    def from_str(cls, data: str):
        return cls.from_obj(tomli.loads(data))

