from typing import List
import re
import astropy.units as u
import pandas as pd
# from icecream import ic
from .command import Command, section, command
from .util import parse_conversions

NS_PER_SEC = 1000 * 1000 * 1000

UNITS = {
  'inch': '0.0254 m',
  'foot': '0.3048 m',
  'yard': '3 foot',
  'mile': '5280 foot',

  'minute': '60 s',
  'hour': '60 minute',
  'day': '24 hour',
  'week': '7 day',

  # 'mph': '1 mile / hour',
  'kmph': '1 km / hour',
}

UNIT_ALIASES = {
  'in': 'inch',
  'ft': 'foot',
  'yd': 'yard',
  'mi': 'mile',
  'sec': 's',
  'min': 'minute',
  'hr': 'hour',
  'd': 'day',
  'wk': 'week',
  'w': 'week',
}

def define_a_bunch_more_units():
  units = {}
  for name, quantity in UNITS.items():
    base_quantity = u.Unit(quantity)
    unit = units[name] = u.def_unit(name, base_quantity)
    u.add_enabled_units([unit])
  # ic(units)
  # u.add_enabled_units(units.values())

  aliases = {
    alias: (units.get(name) or u.Unit(name))
    for alias, name in UNIT_ALIASES.items()
  }
  # ic(aliases)
  u.add_enabled_aliases(aliases)

define_a_bunch_more_units()

###############################################

section('Types', 50)

@command
class Unit(Command):
  '''
  unit - Convert units.

  Aliases: convert

  Arguments:

  COL:UNITS:...      |  Connvert column to unit.
  DST=SRC:UNITS:...  |  Set DST column to conversion of SRC.

  Examples:

  # Convert column c from feet to meters:
  $ psv in a.csv // unit c_in_meters=c:ft:m // md

  '''
  def xform(self, inp, _env):
    conversions = parse_conversions(inp, self.args)
    out = inp.copy()
    for out_col, inp_col, out_units in conversions:
      out[out_col] = self.convert_col(out, inp_col, out_units)
    return out

  def convert_col(self, out, inp_col: str, out_units: List[str]):
    seq = out[inp_col]
    for out_unit in out_units:
      out_unit = re.sub(r'-', ' ', out_unit)
      seq = self.convert_seq_unit(seq, out_unit)
    return seq

  def convert_seq(self, seq, out_unit: str):
    inp_type = seq.dtype
    return self.convert_seq_type(seq, inp_type, out_unit)

  def convert_seq_unit(self, seq, out_unit: str):
    def convert(val):
      unit = u.Unit(out_unit)
      if isinstance(val, (float)):
        result = val * unit
      else:
        result = val.to(unit)
      # ic((val, unit, result))
      return result
    seq = seq.apply(convert)
    return seq

  def convert_to_numeric(self, seq):
    inp_type = seq.dtype.name
    if inp_type in ('float', 'float32', 'float64'):
      return seq
    if inp_type in ('int', 'int32', 'int64'):
      return seq
    if inp_type in ('timedelta64'):
      return seq.total_seconds()
    if inp_type in ('datetime64'):
      return seq.astype('int64').astype('float64') / NS_PER_SEC
    return pd.to_numeric(seq, downcast='float', errors='coerce')
