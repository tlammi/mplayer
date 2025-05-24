import asyncio
from datetime import timedelta, time
from typing import AsyncGenerator


def _get_unit(s: str):
    if s in ("ms", "millisecond", "milliseconds"):
        return "milliseconds"
    if s in ("s", "sec", "second", "seconds"):
        return "seconds"
    if s in ("m", "min", "minute", "minutes"):
        return "minutes"
    if s in ("h", "hour", "hours"):
        return "hours"
    if s in ("d", "day", "days"):
        return "days"
    raise ValueError(f"Unsupported unit: {s}")


def _find_first(sequence, predicate):
    for i, v in enumerate(sequence):
        if predicate(v):
            return i, v
    return None, None


def parse_timedelta(s: str):
    """
    Parse timedelta from string
    """
    orig = s
    ints = []
    units = []
    while True:
        s = s.lstrip()
        if not s:
            break
        if not s[0].isdigit():
            raise ValueError(f"Invalid duration string: '{orig}'")
        i, _ = _find_first(s, lambda c: not c.isdigit())
        ints.append(int(s[:i]))
        s = s[i:]
        i, _ = _find_first(s, lambda c: c.isdigit())
        if i is None:
            units.append(s)
            break
        units.append(s[:i])
        s = s[i:]
    assert len(ints) == len(units)

    map = {_get_unit(u.strip()): i for u, i in zip(units, ints)}
    return timedelta(**map)

def parse_time_overflow(s: str) -> tuple[time, int]:
    """
    Parse ISO time format (12:23:34) while allowing hour overflows.

    Maximum value is 99:59:59

    :return: Parsed time with overflows removed + number of days overflowed
    """
    err = ValueError(f"Invalid time: '{s}'")
    parts = s.split(":")
    if any(len(p) != 2 for p in parts):
        raise err
    for p in parts:
        for c in p:
            if c > '9' or c < '0':
                raise err
    days=0
    hours=0
    mins=0
    secs=0
    part = parts.pop(0).lstrip('0')
    if part:
        hours = int(part)
    while(hours > 23):
        hours -= 24
        days += 1
    if parts:
        part = parts.pop(0).lstrip("0")
        if part:
            mins = int(part)
    if parts:
        part = parts.pop(0).lstrip("0")
        if part:
            secs = int(part)
    return time(hours, mins, secs), days



async def multiplex(*generators: AsyncGenerator) -> AsyncGenerator:
    End = object()
    q = asyncio.Queue()
    async def task(generator: AsyncGenerator):
        async for item in generator:
            await q.put(item)
        await q.put(End)

    async with asyncio.TaskGroup() as tg:
        for g in generators:
            tg.create_task(task(g))
        finished = 0
        count = len(generators)
        while finished < count:
            item = await q.get()
            if item is End:
                finished += 1
            else:
                yield item
