from typing import Any, List
import re
import ipaddress
from devdriven.util import split_flat
import astropy.units as u
import pandas as pd
# from icecream import ic
from .command import Command, section, command
from .util import parse_column_and_opt

NS_PER_SEC = 1000 * 1000 * 1000

section('Types', 50)

@command
class Convert(Command):
  '''
  convert - Convert units.
  Aliases: u

  Arguments:

  COL:UNIT ...  |  Column to convert to unit.

  Examples:

  $ psv in us-states.csv // shuffle // head 10 // cut State,Population // csv- // o us-states-sample.csv
  $ psv in us-states-sample.csv // sort Population
  $ psv in us-states-sample.csv // coerce Population:int // sort Population

  # Convert date string to datetime64 to UNIX epoch to datetime64:
  $ psv i example/birthdays.csv // '''
  ''' copy birthday:parsed_dt // coerce parsed_dt:datetime // '''
  '''cp parsed_dt:unix_epoch // coerce unix_epoch:epoch // cp unix_epoch:unix_dt // coerce unix_dt:datetime
  '''
  def xform(self, inp, _env):
    inp_cols = list(inp.columns)
    out_types = [parse_column_and_opt(inp_cols, arg) for arg in split_flat(self.args, ',')]
    out = inp.copy()
    for imp_col, out_types in out_types:
      out[imp_col] = self.convert_col(out, imp_col, out_types.split(':'))
    return out

  def convert_col(self, out, inp_col: str, out_types: List[str]):
    seq = out[inp_col]
    inp_type = seq.dtype
    for out_type in out_types:
      out_type = re.sub(r'-', '_', out_type)
      seq = self.convert_seq_type(seq, inp_col, inp_type, out_type)
      ic((inp_col, inp_type, out_type, seq.to_list()))
      inp_type = out_type
    return seq

  def convert_seq(self, seq, out_type: str):
    inp_type = seq.dtype
    return self.convert_seq_type(seq, inp_type, out_type)

  def convert_seq_unit(self, seq, out_unit: str):
    def convert(val):
      unit = u.getattr(out_unit)
      if isinstance(val, (float)):
        return val * unit
      return val.to_value(unit) * unit
    seq = seq.apply(convert)
    return seq

  def convert_to_float(self, seq):
    inp_type = seq.dtype.name
    if inp_type in ('timedelta64'):
      return seq.total_seconds()
    if inp_type in ('datetime64'):
      return seq.astype('int64').astype('float64') / NS_PER_SEC
    if inp_type in ('str'):
      seq = remove_commas(seq)
    return pd.to_numeric(seq, downcast='float', errors='coerce')

  unit_aliases = {
    'n': 'numeric',
    'i': 'int',
    'int32': 'int',
    'int64': 'int',
    'f': 'float',
    'epoch': 'epoch',
    'unix': 'epoch',
    'sec': 'timedelta_second',
    'secs': 'timedelta_second',
    's': 'timedelta_second',
    'minutes': 'timedelta_minute',
    'min': 'timedelta_minute',
    'timedelta_h': 'timedelta_hour',
    'hour': 'timedelta_hour',
    'hours': 'timedelta_hour',
    'hr': 'timedelta_hour',
    'h': 'timedelta_hour',
    'day': 'timedelta_day',
    'days': 'timedelta_day',
    'd': 'timedelta_day',
    'week': 'timedelta_week',
    'weeks': 'timedelta_week',
    'wk': 'timedelta_week',
    'w': 'timedelta_week',
    'year': 'timedelta_year',
    'years': 'timedelta_year',
    'yr': 'timedelta_year',
    'y': 'timedelta_year',
  }

  SEC_TO_UNIT = {
    'nanosecond': 1e-9,
    'microsecond': 1e-6,
    'millisecond': 1e-3,
    'second': 1,
    'minute': 60,
    'hour': 60 * 60,
    'day': 60 * 60 * 24,
    'week': 60 * 60 * 24 * 7,
    'year': 60 * 60 * 24 * 365.25,
    'century': 60 * 60 * 24 * 365.25 * 100,
    'millennium': 60 * 60 * 24 * 365.25 * 100,
  }

def remove_commas(seq, inp_type):
  if inp_type in (object, str):
    return seq.apply(lambda x: str(x).replace(',', ''))
  return seq

