"""
Scheduling
"""

import os

from dataclasses import dataclass
from datetime import datetime, date, timedelta, time

import tomllib

from . import util

def __is_date(s: str):
    return len(s.split("-")) == 3

def __is_time(s: str):
    parts = s.split(":")
    if len(parts) > 3:
        return False
    if any(len(p) != 2 for p in parts):
        return False
    for p in parts:
        for c in p:
            if c > '9' or c < '0':
                return False
    return True

def _to_dt_from_str(s: str, curr_date: date) -> datetime | date:
    err = ValueError(f"Could not parse datetime/date/time from '{s}'")
    parts = s.split(" ")
    parts = [s for p in s.split(" ") for s in p.split("T")]
    if len(parts) > 2:
        raise err
    if len(parts) == 2:
        tm, overflow = util.parse_time_overflow(parts[1])
        dt = date.fromisoformat(parts[0]) + timedelta(days=overflow)
        return datetime.combine(dt, tm)
    value = parts[0]
    if __is_date(value):
        return date.fromisoformat(value)
    if __is_time(value):
        tm, overflow = util.parse_time_overflow(value)
        return datetime.combine(curr_date + timedelta(days=overflow), tm)
    raise err


def _to_datetime(val: datetime | date | time | str, dt: date) -> datetime:
    if isinstance(val, str):
        return _to_datetime(_to_dt_from_str(val, dt), dt)
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    return datetime.combine(dt, val)

def _to_timedelta(val: timedelta | time):
    if isinstance(val, timedelta):
        return val
    return timedelta(hours=val.hour, minutes=val.minute, seconds=val.second)

class _InvalidEventError(ValueError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


@dataclass
class Event:
    playlist: str
    at: datetime

    @staticmethod
    def from_obj(d: dict, dt: date|None = None)->"Event":
        dt = dt if dt is not None else datetime.now().date()
        try:
            return Event(d["playlist"], _to_datetime(d["at"], dt))
        except KeyError:
            raise _InvalidEventError("Invalid event")

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
        active_date = datetime.now().date()
        for obj in data.get("schedule", []):
            try:
                evt = Event.from_obj(obj, active_date)
                active_date = evt.at.date()
                s.append(evt)
            except _InvalidEventError:
                s.append(OffsetEvent.from_obj(obj))
        if enums:
            for item in s:
                if item.playlist not in enums:
                    raise ValueError(f"Invalid playlist: {item.playlist}")
        if s and isinstance(s[0], OffsetEvent):
            raise ValueError("Offset event cannot be first event")
        return s

    @classmethod
    def from_str(cls, data: str):
        return cls.from_obj(tomllib.loads(data))

    @classmethod
    def from_file(cls, path: os.PathLike) -> "RawSchedule":
        with open(path, "rb") as f:
            return cls.from_obj(tomllib.load(f))

class Schedule(list[Event]):
    """
    Processed schedule where offsets are resolved to time points
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def from_raw(raw: RawSchedule) -> "Schedule":
        res = Schedule()
        for i in raw:
            if isinstance(i, Event):
                res.append(i)
            else:
                res.append(i.absolute(res[-1]))
        prev_dt = datetime.min
        for i in res:
            if i.at < prev_dt:
                raise ValueError("Scheduled events not in order")
            prev_dt = i.at
        return res

    @classmethod
    def from_obj(cls, data: dict) -> "Schedule":
        return cls.from_raw(RawSchedule.from_obj(data))

    @classmethod
    def from_str(cls, data: str) -> "Schedule":
        return cls.from_raw(RawSchedule.from_str(data))

    @classmethod
    def from_file(cls, path: os.PathLike) -> "Schedule":
        return cls.from_raw(RawSchedule.from_file(path))
