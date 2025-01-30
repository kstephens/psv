import pandas as pd
import psv.util as sut


def test_get_columns():
    df = make_dataframe()
    assert sut.get_columns(df) == ["A", "B", "C"]
    assert sut.get_columns(["X", "Y"]) == ["X", "Y"]


def test_parse_column_and_opt():
    cols = ["A", "B"]
    assert sut.parse_column_and_opt(cols, "A") == ("A", None)
    assert sut.parse_column_and_opt(cols, "B:foo") == ("B", "foo")


def test_parse_col_or_index():
    cols = ["A", "B", "C"]
    assert sut.parse_col_or_index(cols, "B") == "B"
    assert sut.parse_col_or_index(cols, "1") == "A"
    assert sut.parse_col_or_index(cols, "@1") == "A"
    assert sut.parse_col_or_index(cols, "-1") == "C"


def test_select_columns():
    cols = ["A", "B", "C"]

    def fut(cols, args):
        return sut.select_columns(cols, args)

    assert fut(cols, ["A"]) == ["A"]
    assert fut(cols, ["*"]) == cols
    assert fut(cols, ["*", "B:-"]) == ["A", "C"]
    assert fut(cols, ["B", "*:-", "A"]) == ["A"]  # ???: expect []'B', 'A']


def test_parse_conversions():
    fut = sut.parse_conversions
    assert fut(["A", "B", "C"], ["A:T1:T2", "@2:T3", "D=C:T4"]) == [
        ("A", "A", ["T1", "T2"]),
        ("B", "B", ["T3"]),
        ("D", "C", ["T4"]),
    ]


def make_dataframe():
    return pd.DataFrame({"A": [2, 3], "B": [5, 7], "C": [11, 13]})
