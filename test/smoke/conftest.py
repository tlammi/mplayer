import sys
from subprocess import run, PIPE, Popen
from pathlib import Path
import pytest
import pytest_xvfb


@pytest.fixture(autouse=True, scope="session")
def ensure_xvfb():
    if not pytest_xvfb.has_executable("Xvfb"):
        raise OSError("Xvfb not found")


@pytest.fixture
def resource_dir():
    return (Path(__file__).parent / "resources").resolve()


@pytest.fixture
def mplayer():
    def wrap(*args):
        return run(
            [sys.executable, "-m", "mplayer"] + list(args), stdout=PIPE, check=True
        )

    return wrap


@pytest.fixture
def mplayerd():
    with Popen(["mplayer", "daemon"], stdout=PIPE) as proc:
        yield proc


@pytest.fixture
def mplayerctl():
    def wrap(*args):
        return run(["mplayer", "ctl"] + list(args), stdout=PIPE, check=True)

    return wrap
