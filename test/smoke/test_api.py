import asyncio
import tempfile

from pathlib import Path

import pytest

from mplayer.api import Server, Client


@pytest.fixture
def socket():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d) / "mplayer.sock"


@pytest.mark.asyncio
async def test_no_srv(socket):
    c = Client(socket)
    with pytest.raises(FileNotFoundError):
        await c.ping()


@pytest.mark.asyncio
async def test_ping(socket):
    s = Server(socket)
    tsk = asyncio.create_task(s.run())
    await asyncio.sleep(0)
    c = Client(socket)
    await c.ping()
    tsk.cancel()


@pytest.mark.asyncio
async def test_scan(socket):
    s = Server(socket)
    counter = 0

    async def cb():
        nonlocal counter
        counter += 1

    s.on_scan(cb)
    tsk = asyncio.create_task(s.run())
    await asyncio.sleep(0)
    c = Client(socket)
    await c.scan()
    assert counter == 1
    tsk.cancel()


@pytest.mark.asyncio
async def test_multiscan(socket):
    s = Server(socket)
    counter = 0

    async def cb():
        nonlocal counter
        counter += 1

    s.on_scan(cb)
    tsk = asyncio.create_task(s.run())
    await asyncio.sleep(0)
    c = Client(socket)
    await c.scan()
    await c.scan()
    assert counter == 2
    tsk.cancel()
