#!/usr/bin/env python3

import sys

from pathlib import Path

root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

import asyncio

from mplayer import fs
from mplayer import wdog


async def wait(s: fs.MonitorSet, wd: wdog.Wdog):
    while True:
        await wd.run()
        print(f"static: {s.static}")
        print(f"modified: {s.modified}")
        print(f"created: {s.new}")
        print(f"removed: {s.removed}")
        s.reset()


async def produce(s: fs.MonitorSet, wd: wdog.Wdog):
    async for evt in fs.monitor(Path(sys.argv[1]), recursive=True, ignore_dirs=True):
        s.add(evt)
        await wd.kick()


async def run():
    s = fs.MonitorSet()
    wd = wdog.Wdog(2.0)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(wait(s, wd))
        tg.create_task(produce(s, wd))

def main():
    asyncio.run(run())

if __name__ == "__main__":
    sys.exit(main() or 0)
