import sys
import os
import argparse
import asyncio
import logging
import signal

from datetime import datetime
from pathlib import PurePath

from . import util, plai
from .scheduler import Scheduler
from .schedule import Schedule, Event as SchedEvent
from .config import Config
from .player import Player

_L = logging.getLogger()

def _log_next_event(evt: SchedEvent | None):
    if evt is None:
        next_at = "'never'" if evt is None else str(nxt.at)
        time_until = "NaN" if evt is None else evt.at - datetime.now()
        _L.info(f"Next event at {next_at} (in {time_until})")


async def _consume_schedule(sched: Scheduler, player: Player):
    active = sched.active()
    if active is not None:
        _L.info("Initially active schedule: %s", active.playlist)
        await player.play(active.playlist)
    else:
        _L.info("No active event. Waiting for the first event")
    _log_next_event(sched.next())
    async for evt in sched.event_stream():
        _L.info("Scheduler fired: %s", evt.playlist)
        await player.play(evt.playlist)


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
    p.add_argument("--plai", action=argparse.BooleanOptionalAction, default=None, help="Start plai as a subprogram")
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
    conf.resolve_paths(ns.config)
    if ns.plai is not None and conf.plai is not None:
        conf.plai.run = ns.plai
    async with plai.PlaiProcess(conf.plai):
        async with asyncio.TaskGroup() as tg:
            player = Player(conf)
            tg.create_task(_consume_schedule(sched, player))
            await player.run()

def main():
    ns = _parse_cli()
    logging.basicConfig(level=ns.loglevel.upper(), format="[%(levelname)s] %(message)s")
    try:
        asyncio.run(_run(ns), debug=ns.asyncio_debug)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    sys.exit(main() or 0)
