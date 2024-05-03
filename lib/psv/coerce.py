from typing import List, Dict  # Any,
import re
import ipaddress
import pandas as pd
# from icecream import ic
from .command import Command, section, command
from .util import parse_conversions

section('Types', 50)

NS_PER_SEC = 1000 * 1000 * 1000
TYPE_ALIASES = {
  'n': 'numeric',
  'i': 'int',
  'int32': 'int',
  'int64': 'int',
  'f': 'float',
  's': 'seconds',
  'sec': 'seconds',
  'timedelta': 'timedelta64',
  'td': 'timedelta64',
  'datetime': 'datetime64',
  'dt': 'datetime64',
  'ip': 'ipaddress',
  'ipaddr': 'ipaddress',
  'epoch': 'unix_epoch',
  'unix': 'unix_epoch',
}

ALIAS_DOCS = '\n'.join([
  f'* {f"`{k}`":12s}  -  Alias for `{v}`.'
  for k, v in TYPE_ALIASES.items()
])

@command
class Coerce(Command):
  __doc__ = f'''
  coerce - Coerce column types.
  Aliases: astype

  Arguments:

  COL:TYPES:... ...      |  Coerce COL by TYPES.
  DST=SRC:TYPES:... ...  |  Set DST column to coersion of SRC.

  TYPES:

* `numeric`     -  `int64` or `float64`.
* `int`         -  `int64`.
* `float`       -  `float64`.
* `timedelta64` -  `timedelta64[ns]`.
* `datetime`    -  `datetime`.
* `unix_epoch`  -  Seconds since 1970.
* `ipaddress`   -  Convert to `ipaddress`.

  TYPE Aliases:

{ALIAS_DOCS}

  Examples:

  $ psv in us-states.csv // shuffle // head 10 // cut State,Population // csv- // o us-states-sample.csv
  $ psv in us-states-sample.csv // sort Population
  $ psv in us-states-sample.csv // tr -d ', ' Population // coerce Population:int // sort Population

  # Parse date, convert to datetime, then integer Unix epoch seconds:
  $ psv in birthdays.csv // coerce sec_since_1970=birthday:datetime:epoch:int

  '''
  def xform(self, inp, _env):
    conversions = parse_conversions(inp, self.args)
    out = inp.copy()
    for out_col, inp_col, out_types in conversions:
      out[out_col] = self.coerce_col(out, inp_col, out_types)
    return out

  def coerce_col(self, out, inp_col: str, out_types: List[str]):
    seq = out[inp_col]
    inp_type = seq.dtype.name
    for out_type in out_types:
      out_type = re.sub(r'-', '_', out_type)
      seq = self.coerce_seq_type(seq, inp_type, out_type)
      # ic((inp_col, inp_type, out_type, seq.to_list()))
      inp_type = seq.dtype.name
    return seq

  def coerce_seq(self, seq, out_type: str):
    return self.coerce_seq_type(seq, seq.dtype.name, out_type)

  def coerce_seq_type(self, seq, inp_type: str, out_type: str):
    out_type = TYPE_ALIASES.get(out_type, out_type)
    coercer = self.coercer(out_type)
    return coercer(seq, inp_type)

  def coercer(self, out_type: str):
    return getattr(self, f'_coerce_to_{out_type}')

  def _coerce_to_numeric(self, seq, inp_type: str):
    return pd.to_numeric(seq, errors='coerce')

  def _coerce_to_int(self, seq, inp_type: str):
    return pd.to_numeric(seq, downcast='integer', errors='coerce')

  def _coerce_to_float(self, seq, inp_type: str):
    return pd.to_numeric(seq, downcast='float', errors='coerce')

  def _coerce_to_str(self, seq, _inp_type: str):
    return map(str, seq.tolist())

  def _coerce_to_unix_epoch(self, seq, inp_type: str):
    if inp_type in ('float', 'int'):
      return seq
    seq = self.coerce_seq(seq, 'datetime')
    # ic(seq.dtype.name)
    if seq.dtype.name.startswith('datetime64[ns'):
      seq = seq.astype('int64').astype('float64') / NS_PER_SEC
    return seq

  def _coerce_to_datetime64(self, seq, inp_type: str):
    # ic(inp_type)
    if inp_type in ('float', 'float8', 'float64', 'int', 'int32', 'int64'):
      return pd.to_datetime(seq, unit='s', origin='unix', errors='ignore', cache=True)
    if inp_type.startswith('datetime'):
      return seq
    return pd.to_datetime(
      seq,
      errors='ignore',
      cache=True,
      format='mixed',
      # UserWarning: The argument 'infer_datetime_format' is deprecated and will be removed in a future version.
      # A strict version of it is now the default,
      # see https://pandas.pydata.org/pdeps/0004-consistent-to-datetime-parsing.html.
      # You can safely remove this argument.
      # infer_datetime_format=True,
      utc=self.opt('utc', True)
    )

  def _coerce_to_timedelta64(self, seq, inp_type: str):
    # ic(inp_type)
    if inp_type in ('timedelta64'):
      return seq
    if inp_type in ('float', 'int', 'int32', 'int64'):
      return pd.to_timedelta(seq, unit='s', errors='ignore')
    return pd.to_timedelta(seq, errors='ignore')

  def _coerce_to_seconds(self, seq, _inp_type: str):
    if not seq.dtype.name.startswith('datetime'):
      seq = pd.to_timedelta(seq) # , errors='ignore'
    seq = seq.dt.total_seconds()
    return seq

  def _coerce_to_ipaddress(self, seq, inp_type: str):
    cache: Dict[str, ipaddress.IPv4Address] = {}
    def to_ipaddr(val):
      try:
        if inp_type in ('str'):
          if val in cache:
            return cache[val]
          cache[val] = ipaddr = ipaddress.ip_address(val)
          # ic(type(ipaddr))
          return ipaddr
        return None
      except ValueError:
        return None
    return seq.apply(to_ipaddr)
