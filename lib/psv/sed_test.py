import re
import psv.sed as sut


def test_create_scans():
    fut = sut.create_scans
    cols = ["A", "B", "C"]
    opts = {}

    def opt(name):
        return opts.get(name)

    assert fut(cols, ["*", "S", "R"], opt) == [
        ["A", "S", "R", re.compile("S")],
        ["B", "S", "R", re.compile("S")],
        ["C", "S", "R", re.compile("S")],
    ]

    opts = {"ignore-case": True}
    assert fut(cols, ["B", "S1", "R1", "C", "S2*", "R2"], opt) == [
        ["B", "S1", "R1", re.compile("S1", re.IGNORECASE)],
        ["C", "S2*", "R2", re.compile("S2*", re.IGNORECASE)],
    ]

    opts = {"fixed-strings": True}
    assert fut(cols, ["C", "S2*", "R2"], opt) == [
        ["C", "S2*", "R2", re.compile("S2\\*")],
    ]
