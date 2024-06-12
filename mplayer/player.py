import os

from abc import ABC, abstractmethod


class Player(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    async def play(self, file: os.PathLike):
        pass
