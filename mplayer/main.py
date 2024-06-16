import sys
import os
import argparse
import asyncio
import logging
import signal

from . import api, util
from .app import App
from .playlist import PlaylistSpec, Entry as PlaylistEntry
from .schedule import Schedule
from .core import Core, make_core


_DEFAULT_SOCKET = os.environ.get("MPLAYER_SOCKET", "/tmp/foo.sock")

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
        "--debug",
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
    sp = p.add_subparsers(dest="cmd")
    play = sp.add_parser("play", help="Play files")
    play.add_argument(
        "-f",
        "--fullscreen",
        default=False,
        action=argparse.BooleanOptionalAction,
        help="run in fullscreen",
    )
    play.add_argument(
        "--image-duration",
        default=None,
        type=util.parse_timedelta,
        help="Image duration, e.g. '10s'",
    )
    play.add_argument(
        "--repeat",
        action=argparse.BooleanOptionalAction,
        help="Repeat the files",
        default=False,
    )
    play.add_argument(
        "--schedule",
        help="Read schedule from file. Implies --repeat. "
        "This affects what playlists will be played at what time. "
        "Playlists need to be passed via positional arguments. "
        "Non-playlist files are part of nameless playlists.",
    )
    play.add_argument("files", help="Files to play", nargs="*")

    daemon = sp.add_parser("daemon", help="launch mplayerd")
    daemon.add_argument("-s", "--socket", help="socket path")

    ctl = sp.add_parser("ctl", help="mplayerctl for controlling mplayerd")
    ctl.add_argument("-s", "--socket", help="daemon socket path")
    ctl_sp = ctl.add_subparsers(dest="ctl_cmd")
    ctl_play = ctl_sp.add_parser("play", help="play files")
    ctl_play.add_argument("files", help="files to play", nargs="*")
    return p.parse_args()


async def _run(ns: argparse.Namespace):
    """
    Run the player in foreground mode
    """
    core = await make_core(ns.files, ns.schedule)
    asyncio.get_running_loop().add_signal_handler(signal.SIGHUP, core.request_rescan)
    app = App(core)
    if ns.image_duration is not None:
        await app.set_image_duration(ns.image_duration)
    await app.set_fullscreen(ns.fullscreen)
    await app.set_repeat(ns.repeat or bool(ns.schedule))
    await app.play()


async def _run_daemon(ns: argparse.Namespace):
    sock = ns.socket or _DEFAULT_SOCKET
    srv = api.Server()

    async def on_echo(msg: str):
        return msg

    srv.route("echo", echoer)

    await api.start_server(sock, api.Server())
    await asyncio.sleep(10)


async def _run_ctl(ns: argparse.Namespace):
    sock = ns.socket or _DEFAULT_SOCKET
    c = api.Client(sock)
    res = await c.echo("asdfsdaf")
    print("responded with: ", res)
    pass


async def _main_coro(ns: argparse.Namespace):
    def on_sigint():
        _L.info("SIGINT received. Shutting down")
        for t in asyncio.all_tasks():
            t.cancel()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, on_sigint)
    if ns.cmd == "play":
        await _run(ns)
    elif ns.cmd == "daemon":
        await _run_daemon(ns)
    elif ns.cmd == "ctl":
        await _run_ctl(ns)
    else:
        raise ValueError(f"Unknown command {ns.cmd}")


def main():
    ns = _parse_cli()
    logging.basicConfig(level=ns.loglevel.upper(), format="[%(levelname)s] %(message)s")
    try:
        asyncio.run(_main_coro(ns), debug=ns.debug)
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    sys.exit(main() or 0)
