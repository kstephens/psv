from .pipeline import Parser


def test_parse():
    def parse(argv):
        return Parser().parse(argv)

    assert not parse([])
    assert parse(["a"]) == [["a"]]
    assert parse(["a", "b"]) == [["a", "b"]]
    assert parse(["a", "b", "//", "c"]) == [["a", "b"], ["c"]]
    assert parse(["//", "c"]) == [["c"]]
    assert parse(["a", "{{", "b", "//", "c", "}}", "d", "//", "e", "f"]) == [
        ["a", "{{", "b", "//", "c", "}}", "d"],
        ["e", "f"],
    ]


def test_parse_recur():
    def parse(argv):
        return Parser().parse(argv, recur=True)

    assert not parse([])
    assert parse(["a"]) == [["a"]]
    assert parse(["a", "//", "b", "c", "//"]) == [["a"], ["b", "c"]]
    assert parse(["a", "//", "b", "{{", 1, 2, "}}", "c", "//", "d"]) == [
        ["a"],
        ["b", [1, 2], "c"],
        ["d"],
    ]
    # Assert exception:
    # scan(['a', '//', 'b', '{{', '}}', 'c'], [['a'], ['b']])
