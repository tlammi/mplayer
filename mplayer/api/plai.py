import os
import time

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
        return Session(transport=tport, timeout=5.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def ping(self):
        req = self._mk_request("GET", "_ping")
        return self.send(req)


    async def play(self, playlist: list[str]):
        playlist = [f"image/{i}" for i in playlist]
        req = self._mk_request("POST", "play", json=playlist, params={"replay": "true"})
        await self.send(req)

    async def list_medias(self) -> list[str]:
        req = self._mk_request("GET", "media/image")
        res = await self.send(req)
        res.raise_for_status()
        lst = res.json()
        if not isinstance(lst, list):
            raise TypeError(f"Unexpected response format from frontend: {lst}")
        return [i["key"] for i in lst]

    async def upload_media(self, key: str, path: os.PathLike|str, chunk_size=1024):
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
        req = self._mk_request("GET", f"media/image/{key}")
        res = await self.send(req)
        res.raise_for_status()
        obj = res.json()
        if not isinstance(obj, dict):
            raise TypeError(f"Expected JSON from API. Got {obj}")
        return MediaMeta(**obj)

    async def delete_media(self, key: str) -> bool:
        req = self._mk_request("DELETE", f"media/image/{key}")
        res = await self.send(req)
        return res.is_success

    def _mk_request(self, mthd: str, path: str, **kwargs):
        return self.build_request(mthd, "http://_/plai/v1/" + path, **kwargs)

