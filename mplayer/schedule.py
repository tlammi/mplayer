"""
Scheduling
"""


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


    def absolute(self, prev: Event) -> Event:
        """
        Convert offset event to absolute

        This adds the time offset specified in self to the previous event and
        returns a new Event corresponding to this OffsetEvent.
        """

        return Event(playlist=self.playlist, at=prev.at+self.offset)


    @staticmethod
    def from_obj(d: dict) -> "OffsetEvent":
        return OffsetEvent(playlist=d["playlist"], offset=_to_timedelta(d["offset"]))


class RawSchedule(list[Event|OffsetEvent]):
    """
    Schedule as parsed directly from a file.
    """
    def __init__(self):
        pass

    @staticmethod
    def from_obj(data: dict) -> "RawSchedule":
        s = RawSchedule()
        enums = data.get("playlists", [])
        for obj in data.get("schedule", []):
            try:
                s.append(Event.from_obj(obj))
            except ValueError:
                s.append(OffsetEvent.from_obj(obj))
        if enums:
            for item in s:
                if item.playlist not in enums:
                    raise ValueError(f"Invalid playlist: {item.playlist}")
        return s

    @classmethod
    def from_str(cls, data: str):
        return cls.from_obj(tomli.loads(data))

class Schedule(list[Event]):
    """
    Processed schedule where offsets are resolved to time points
    """
    pass
