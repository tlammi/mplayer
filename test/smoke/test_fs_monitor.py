import asyncio
import tempfile

from pathlib import Path
from typing import AsyncGenerator, TypeVar

import pytest

from mplayer import fs

async_ = pytest.mark.asyncio

create_task = asyncio.create_task

@pytest.fixture(scope="function")
def tmpdir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


T = TypeVar("T")

async def get_first(async_gen: AsyncGenerator[T]) -> T:
    async for i in async_gen:
        return i
    assert False

@async_
async def test_cancel(tmpdir):
    q = asyncio.Queue()
    async def void():
        q.put_nowait(None)
        async for _ in fs.monitor(tmpdir):
            pass
    task = create_task(void())
    await q.get()
    task.cancel()

@async_
async def test_touch(tmpdir):
    file = tmpdir / "foo"

    async def toucher():
        file.touch()
    create_task(toucher())
    evt = await get_first(fs.monitor(tmpdir, ignore_dirs=True, events={fs.EventType.Created}))
    assert evt.src == Path("foo")
    assert evt.kind == fs.EventType.Created

@async_
async def test_rm(tmpdir):
    file = tmpdir / "foo"
    async def cycler():
        file.touch()
        file.unlink()
    create_task(cycler())
    evt = await get_first(fs.monitor(tmpdir, ignore_dirs=True, events={fs.EventType.Deleted}))
    assert evt.src == Path("foo")
    assert evt.kind == fs.EventType.Deleted

