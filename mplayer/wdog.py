import asyncio

from datetime import timedelta, datetime


class Wdog:
    """
    Watchdog

    The run() method will block until kick() is not called within the configured interval
    """

    def __init__(self, timeout: timedelta | float):
        self._to = timeout.total_seconds() if isinstance(timeout, timedelta) else timeout
        self._q: asyncio.Queue[bool] = asyncio.Queue()

    async def run(self):
        while True:
            try:
                bite = await asyncio.wait_for(self._q.get(), self._to)
                if bite:
                    return
            except TimeoutError:
                return

    async def kick(self):
        await self._q.put(False)

    async def expire(self):
        await self._q.put(True)
