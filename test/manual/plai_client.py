#!/usr/bin/env python3

import sys

from pathlib import Path

root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

import asyncio

from mplayer.api import plai


async def run():
    async with plai.Session.unix_session(sys.argv[1]) as sess:
        res = await getattr(sess, sys.argv[2])()
        print(res)

def main():
    asyncio.run(run())

if __name__ == "__main__":
    sys.exit(main() or 0)
