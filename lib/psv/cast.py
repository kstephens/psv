from .caster import Caster, TYPE_ALIASES
from .command import Command, section, command
from .util import parse_conversions

section("Types", 50)

ALIAS_DOCS = "\n".join(
    [f'* {f"`{k}`":14s}  -  Alias for `{v}`.' for k, v in TYPE_ALIASES.items()]
)


@command
class Cast(Command):
    __doc__ = f"""
  cast - Cast column types.
  Aliases: astype, coerce

  Arguments:

  COL:TYPES:... ...      |  Cast COL by TYPES.
  DST=SRC:TYPES:... ...  |  Set DST column to coersion of SRC.

  TYPES:

* `numeric`     -  `int64` or `float64`.
* `int`         -  `int64`.
* `float`       -  `float64`.
* `str`         -  `str`.
* `timedelta64` -  `timedelta64[ns]`.
* `datetime`    -  `datetime`.
* `unix_epoch`  -  Seconds since 1970.
* `ipaddress`   -  Convert to `ipaddress`.
* `hostname`    -  Convert to hostname by DNS lookup.

  TYPE Aliases:

{ALIAS_DOCS}

  Examples:

  $ psv in us-states.csv // shuffle // head 10 // cut State,Population // csv- // o us-states-sample.csv
  $ psv in us-states-sample.csv // sort Population
  $ psv in us-states-sample.csv // tr -d ', ' Population // cast Population:int // sort Population

  # Parse date, convert to datetime, then integer Unix epoch seconds:
  $ psv in birthdays.csv // cast sec_since_1970=birthday:datetime:epoch:int

  """

    def xform(self, inp, _env):
        conversions = parse_conversions(inp, self.args)
        out = inp.copy()
        caster = self.make_caster()
        for out_col, inp_col, out_types in conversions:
            out[out_col] = caster.cast_col(out, inp_col, out_types)
        return out

    def make_caster(self):
        opts = {"utc": self.opt("utc", True)}
        return Caster(TYPE_ALIASES, opts)
