import asyncio

from datetime import timedelta, datetime


class Wdog:
    """
    Watchdog

    The run() method will block until kick() is not called within the configured interval
    """

    def __init__(self, timeout: timedelta | float, *, initial_block = False):
        """
        Setup a watchdog

        Operation only starts after run() is called

        :param timeout Watchdog deadline
        :param initial_block: Whether the first call should block indefinitely
        """
        self._to = timeout.total_seconds() if isinstance(timeout, timedelta) else timeout
        self._q: asyncio.Queue[bool] = asyncio.Queue()
        self._initial_block = initial_block

    async def run(self):
        if self._initial_block and await self._step(self._q.get()):
            return
        while True:
            if await self._step(asyncio.wait_for(self._q.get(), self._to)):
                return

    async def kick(self):
        await self._q.put(False)

    async def expire(self):
        await self._q.put(True)

    async def _step(self, awaitable) -> bool:
        try:
            bite = await awaitable
            return bite
        except TimeoutError:
            return True

