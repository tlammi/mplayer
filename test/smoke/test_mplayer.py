def test_help(mplayer):
    res = mplayer("--help")
    assert res.stdout


def test_play(mplayer, resource_dir):
    res = mplayer("play", "--image-duration=1s", resource_dir / "vlc.png")
