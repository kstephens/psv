from typing import Callable, List
import re
import pandas as pd
from devdriven.util import chunks
from .command import Command, section, command
from .util import select_columns, get_columns

section("Manipulation", 30)


@command
class Sed(Command):
    """
      sed - Search and replace text.

    Arguments:

      COL SEARCH REPLACE ...    |  Search and Replace in COL.
      --fixed-strings, -F       |  Match fixed string.
      --ignore-case, -i         |  Ignore case distinctions.
      --convert-to-string, -S   |  Convert all data to string first.

    Examples:

    # Replace Population "," with "_":
    $ psv in us-states.csv // sed -F --convert-to-string @4 , _ // head 5 // md
    """

    def xform(self, inp, _env):
        out = inp.copy()
        scans = create_scans(list(inp.columns), self.args, self.opt)
        for col, _search, replace, rx in scans:
            seq = out[col]
            if self.opt("convert-to-string"):
                seq = pd.Series(seq, dtype="string")

            def search_replace(val):
                nonlocal rx, replace
                if val is not None:
                    # pylint: disable-next=cell-var-from-loop
                    return re.sub(rx, replace, val)
                return None

            out[col] = seq.apply(search_replace)
        return out


def create_scans(cols: List[str], args: List[str], opt: Callable):
    cols = get_columns(cols)
    scans = []
    for col, search, replace in chunks(args, 3):
        for col in select_columns(cols, [col], check=True):
            scans.append([col, search, replace])
    for scan in scans:
        rx = scan[1]
        re_opts = 0
        if opt("ignore-case"):
            re_opts = re.IGNORECASE
        if opt("fixed-strings"):
            rx = re.escape(rx)
        rx = re.compile(rx, re_opts)
        scan.append(rx)
    return scans
