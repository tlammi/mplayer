from mplayer.playlist import PlaylistSpec, Playlist, Entry


def test_spec_default():
    p = PlaylistSpec()
    assert len(p) == 0


def test_spec_with_entries():
    p = PlaylistSpec([Entry("a"), Entry("b")])
    assert len(p) == 2


def test_spec_with_filters():
    obj = {
        "name": "test",
        "media": [str(i) for i in range(100)]
        + [{"url": "100", "filters": {"newest": 20}}],
    }
    (p,) = PlaylistSpec.from_yaml([obj])
    assert p.name == "test"
    assert len(p) == 101
    filters = p[100].filters
    assert len(filters) == 1
    assert filters[0].name == "newest"
