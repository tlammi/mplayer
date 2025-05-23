import os

from pathlib import Path
from dataclasses import dataclass

import httpx



@dataclass
class MediaMeta:
    size: int
    sha256: str


class Session(httpx.AsyncClient):

    @staticmethod
    def unix_session(uds: str) -> "Session":
        tport = httpx.AsyncHTTPTransport(uds=uds)
        return Session(transport=tport)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def ping(self):
        req = self._mk_request("GET", "_ping")
        await self.send(req) 

    async def play(self, playlist: list[str]):
        async def foo():
            return playlist
        req = self._mk_request("POST", "play", json=playlist)
        await self.send(req)


    async def list_medias(self) -> list[str]:
        req = self._mk_request("GET", "media/image")
        res = await self.send(req)
        res.raise_for_status()
        return res.json()

    async def upload_media(self, key: str, path: os.PathLike|str):
        chunk_size = 1024
        async def upload():
            with open(path, "rb") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        req = self._mk_request("PUT", f"media/image/{key}", content=upload())
        res = await self.send(req)
        res.raise_for_status()

    async def inspect_media(self, key: str) -> MediaMeta:
        ...

    async def delete_media(self, key: str):
        ...

    def _mk_request(self, mthd: str, path: str, **kwargs):
        return self.build_request(mthd, "http://_/plai/v1/" + path, **kwargs)

