from typing import List
import re
from devdriven.util import split_flat, get_safe, glob_to_rx
import pandas as pd  # type: ignore

HasCols = List[str] | pd.DataFrame
Cols = List[str]


def get_columns(cols: HasCols) -> Cols:
    if isinstance(cols, pd.DataFrame):
        cols = list(cols.columns)
    return cols


def parse_column_and_opt(cols: HasCols, arg):
    cols = get_columns(cols)
    if m := re.match(r"^([^:]+):(.*)$", arg):
        return parse_col_or_index(cols, m[1]), m[2]
    return parse_col_or_index(cols, arg), None


def select_columns(
    inp: HasCols, args: List[str], check=False, default_all=False
) -> Cols:
    inp_cols = get_columns(inp)
    if not args and default_all:
        return inp_cols
    selected: Cols = []
    for arg in args:
        action = "+"
        col, opts = parse_column_and_opt(inp_cols, arg)
        if m := opts and re.match(r"^([-+]?)(?::(.*))?$", opts):
            action = m[1]
            opts = m[2]
        col_rx = glob_to_rx(col)
        matched_cols = [col for col in inp_cols if re.match(col_rx, col)]
        if not check and not matched_cols:
            matched_cols = [col]
        if action == "-":
            selected = [x for x in selected if x not in matched_cols]
        else:
            selected = selected + [x for x in matched_cols if x not in selected]
    if check:
        if unknown := [col for col in selected if col not in inp_cols]:
            raise Exception(f"unknown columns: {unknown!r} : available {inp_cols!r}")
    return selected


def parse_col_or_index(cols: HasCols, arg: str, check=False) -> str:
    cols = get_columns(cols)
    col = arg
    #  if m := re.match(r'^(?:@(-\d+)|@?(\d+))$', arg):
    #    i = int(m[1] or m[2])
    if m := re.match(r"^@?(-?\d+)$", arg):
        i = int(m[1])
        if i > 0:
            i = i - 1
        col = get_safe(cols, i)
    if check and not col:
        raise Exception(f"unknown column: {col!r} : available {cols!r}")
    return col


def parse_conversions(cols, args):
    cols = get_columns(cols)
    cols_and_types = [parse_column_and_opt(cols, arg) for arg in split_flat(args, ",")]
    conversions = []
    for col, out_types in cols_and_types:
        col = col.split("=", 1)
        out_col, inp_col = col[0], col[-1]
        out_types = out_types and out_types.split(":")
        conversions.append((out_col, inp_col, out_types))
    return conversions
