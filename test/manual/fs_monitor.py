#!/usr/bin/env python3

import sys

from pathlib import Path

root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

import asyncio

from mplayer import fs


async def hello():
    async for evt in fs.monitor(sys.argv[1], recursive=True, ignore_dirs=True):
        print(f"{evt.src} {evt.kind}")

def main():
    asyncio.run(hello())

if __name__ == "__main__":
    sys.exit(main() or 0)
