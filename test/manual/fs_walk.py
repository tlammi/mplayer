#!/usr/bin/env python3

import sys

from pathlib import Path

root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

import asyncio

from mplayer import fs


async def hello():
    path = Path(sys.argv[1])
    filters = sys.argv[2:]
    async for entry in fs.walk(Path(sys.argv[1]), filters=filters, ignore_dirs=True):
        print(entry)

def main():
    asyncio.run(hello())

if __name__ == "__main__":
    sys.exit(main() or 0)
