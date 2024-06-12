import asyncio
import os
from typing import TypeAlias, TypeVar
from collections.abc import Awaitable, Callable


T = TypeVar("T")

OnScan: TypeAlias = Callable[[], Awaitable[None]]


class Server:

    def __init__(self, sock: os.PathLike):
        self._sock = sock
        self._on_scan: OnScan | None = None

    def on_scan(self, cb: OnScan):
        self._on_scan = cb

    async def run(self):
        await asyncio.start_unix_server(self._serve, self._sock)

    async def _serve(self, r: asyncio.StreamReader, w: asyncio.StreamWriter):
        data = await r.read()
        service, *args = data.split(b"\x00")
        if service == b"ping":
            w.write_eof()
            await w.drain()
            return
        if service == b"scan":
            assert self._on_scan is not None
            await self._on_scan()
            w.write_eof()
            await w.drain()
            return
        w.write_eof()
        await w.drain()


class Client:

    def __init__(self, sock: str):
        self._sock = sock

    async def ping(self):
        return await self._request(b"ping")

    async def scan(self):
        return await self._request(b"scan")

    async def _request(self, service: bytes, *args: bytes):
        r, w = await asyncio.open_unix_connection(self._sock)
        w.write(b"\x00".join([service, *args]))
        w.write_eof()
        await w.drain()
        return await r.read()
