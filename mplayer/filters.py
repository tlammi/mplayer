
from abc import ABC, abstractmethod

from pathlib import Path
from typing import AsyncIterator
from asyncio import Event


class Filter(ABC):

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[Path]:
        pass

    @abstractmethod
    def push(self, path: Path):
        pass

class FilterNewest(Filter):
    def __init__(self, count: int):
        self._count = count
        self._queue = []
        self._items = []
        self._not_empty = Event()

    def __aiter__(self) -> AsyncIterator[Path]:
        async def gen():
            await self._not_empty.wait()
            while True:
                if self._queue:
                    self._items.extend(self._queue)
                    self._queue = []
                    self._items.sort(key=lambda x: x.stat().st_mtime)
                    self._items = self._items[-self._count:]
                for i in self._items:
                    yield i
        return gen()

    def push(self, path: Path):
        if not self._items:
            self._not_empty.set()
        self._queue.append(path)
