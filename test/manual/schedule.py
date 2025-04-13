#!/usr/bin/env python3

import sys

from pathlib import Path

root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

import asyncio
from datetime import datetime
from pathlib import Path

from mplayer.schedule import Schedule, Event
from mplayer.scheduler import Scheduler


def _print_next(evt: Event|None):
    if evt is None:
        print("No next event")
        return
    diff = evt.at - datetime.now()
    print(f"Next event at: {evt.at.isoformat()} ({diff})")

async def run():
    schedule = Schedule.from_file(Path(sys.argv[1]))
    sched = Scheduler(schedule)
    _print_next(sched.next())
    async for evt in sched.event_stream():
        print(f"Playlist activated: {evt.playlist}")
        _print_next(sched.next())

def main():
    asyncio.run(run())

if __name__ == "__main__":
    sys.exit(main() or 0)
