import hashlib as hl

from pathlib import PurePath

def sha256(p: PurePath):
    with open(p, "br") as f:
        return hl.sha256(f.read()).hexdigest()


