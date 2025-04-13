import asyncio
import tempfile

from pathlib import PurePath

import pytest

from mplayer import fs

async_ = pytest.mark.asyncio


@pytest.fixture(scope="function")
def tmpdir():
    with tempfile.TemporaryDirectory() as d:
        yield PurePath(d)


@async_
async def test_cancel(tmpdir):
    q = asyncio.Queue()
    async def void():
        q.put_nowait(None)
        async for _ in fs.monitor(tmpdir):
            pass
    task = asyncio.create_task(void())
    await q.get()
    task.cancel()
