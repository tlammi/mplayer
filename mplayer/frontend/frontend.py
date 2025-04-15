from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable
from enum import Enum

class FrontendType(Enum):
    List = "list"

class Frontend(ABC):
    """
    Frontend that actually shows the media files
    """
    @abstractmethod
    def kind(self) -> FrontendType:
        pass

    @abstractmethod
    async def play(self, medias: Iterable[Path]):
        pass

class ListFrontend(Frontend):

    def kind(self) -> FrontendType:
        return FrontendType.List

    async def play(self, medias: Iterable[Path]):
        print("Playing medias:")
        for m in medias:
            print(f"  {m}")

