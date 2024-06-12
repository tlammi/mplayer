from datetime import timedelta


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
