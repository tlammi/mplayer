import os
import shutil
import asyncio
import signal
from typing import Tuple


from config import PlaiConfig



class PlaiProcess:
    """
    Used for (optionally) holding a plai subprocess

    If the configuration does not tell to start the subprocess this does nothing.
    """
    def __init__(self, cfg: PlaiConfig):
        self._cfg = cfg
        self._prog = None

    async def __aenter__(self):
        if not self._cfg.run:
            return
        cmd, args = self._plai_cmd()
        self._prog = await asyncio.create_subprocess_exec(cmd, *args)

    async def __aexit__(self):
        if self._prog is None:
            return
        self._prog.send_signal(signal.SIGINT)
        await self._prog.wait()

    def _plai_cmd(self) -> Tuple[str, list[str]]:
        path = str(self._cfg.path)
        if os.sep in path:
            cmd = path
        else:
            res = shutil.which(path)
            if res is None:
                raise ValueError(f"Cannot find program '{path}'")
            cmd = res
        args = []
        args.append("--socket")
        args.append(str(self._cfg.socket))
        return cmd, args

