import sys
import os
import argparse
import asyncio
import logging
import signal

from datetime import datetime
from pathlib import PurePath

from . import util
from .scheduler import Scheduler
from .schedule import Schedule
from .config import Config

_L = logging.getLogger()

def _parse_cli() -> argparse.Namespace:
    if sys.argv[0].endswith("__main__.py"):
        prog = __name__.split(".")[0]
    else:
        prog = sys.argv[0]
    p = argparse.ArgumentParser(
        prog,
        description="Media player",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "-d",
        "--asyncio-debug",
        help="enable asyncio debugging",
        default=False,
        action=argparse.BooleanOptionalAction,
    )
    p.add_argument("-l", "--loglevel", help="log level", default="info")
    p.add_argument(
        "-v", "--verbose", dest="loglevel", action="store_const", const="debug"
    )
    p.add_argument(
        "-q", "--quiet", dest="loglevel", action="store_const", const="error"
    )
    p.add_argument("--fullscreen", action=argparse.BooleanOptionalAction, default=False, help="Whether to start the frontend in fullscreen")
    p.add_argument("--img-dur", help="Image display duration in seconds", type=float)
    p.add_argument("--blend", help="Media blend duration in seconds", type=float)
    p.add_argument("--watermark", help="Watermark image")
    p.add_argument("--watermark-h", help="Watermark height scaling")
    p.add_argument("--watermark-w", help="Watermark width scaling")
    p.add_argument("--watermark-pos", help="Watermark position (tl, tm, tr, mr, mm, mr, br, bm, bl)", type=str)
    p.add_argument("-c", "--config", help="Path to config", type=PurePath, required=True)
    p.add_argument("-s", "--schedule", help="Path to schedule", type=PurePath, required=True)
    return p.parse_args()

async def _run(ns: argparse.Namespace):
    def on_sigint():
        _L.info("SIGINT received. Shutting down")
        for t in asyncio.all_tasks():
            t.cancel()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, on_sigint)
    sched = Scheduler(Schedule.from_file(ns.schedule))
    conf = Config.from_file(ns.config)
    active = sched.active()
    if active is None:
        nxt = sched.next()
        nxt_at = "'never'" if nxt is None else str(nxt.at)
        time_until = "NaN" if nxt is None else nxt.at - datetime.now()
        _L.info(f"No active event in schedule. Next event at {nxt_at} (in {time_until})")

def main():
    ns = _parse_cli()
    logging.basicConfig(level=ns.loglevel.upper(), format="[%(levelname)s] %(message)s")
    try:
        asyncio.run(_run(ns), debug=ns.asyncio_debug)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    sys.exit(main() or 0)
