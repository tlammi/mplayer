#!/usr/bin/env python3

import sys
import json

from pathlib import Path

root = Path(__file__).parent.parent.parent.resolve()
sys.path.insert(0, str(root))

import asyncio

from mplayer.api import plai


async def run():
    async with plai.Session.unix_session(sys.argv[1]) as sess:
        job = sys.argv[2]
        args = sys.argv[3:]
        if job == "list":
            res = await sess.list_medias()
            print(res)
        elif job == "play":
            res = await sess.play(json.loads(args[0]))
            print(res)
        elif job == "upload":
            res = await sess.upload_media(args[0], args[1])
            print(res)
        else:
            raise ValueError(f"Unsupported command: {job}")

def main():
    asyncio.run(run())

if __name__ == "__main__":
    sys.exit(main() or 0)
