
from mplayer.schedule_doc import ScheduleDoc


def test_init_empty():
    s = ScheduleDoc()
    assert len(s) == 0

