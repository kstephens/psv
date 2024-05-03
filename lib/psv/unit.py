from typing import List, Dict
import re
import pandas as pd
# from icecream import ic
from devdriven import lazy_import
u = lazy_import.load('astropy.units')
from .command import Command, section, command
from .util import parse_conversions

def define_units(units: Dict[str, str], aliases: Dict[str, str] = {}):
  new_units = {}
  for name, quantity in units.items():
    base_quantity = u.Unit(quantity)
    unit = new_units[name] = u.def_unit(name, base_quantity)
    u.add_enabled_units([unit])
  # ic(units)
  # u.add_enabled_units(units.values())

  new_aliases = {
    alias: (new_units.get(name) or u.Unit(name))
    for alias, name in aliases.items()
  }
  # ic(aliases)
  u.add_enabled_aliases(new_aliases)

###############################################

NS_PER_SEC = 1000 * 1000 * 1000

UNITS = {
  'inch': '0.0254 m',
  'foot': '0.3048 m',
  'yard': '3 foot',
  'mile': '5280 foot',
  'marathon': '26.2 mile',

  'minute': '60 s',
  'hour': '60 minute',
  'day': '24 hour',
  'week': '7 day',

  # 'mph': '1 mile / hour',
  'kmph': '1 km / hour',
}

UNIT_ALIASES = {
  'in': 'inch',
  'inches': 'inch',
  'ft': 'foot',
  'feet': 'foot',
  'yd': 'yard',
  'mi': 'mile',
  'miles': 'mile',
  'sec': 's',
  'min': 'minute',
  'hr': 'hour',
  'd': 'day',
  'wk': 'week',
  'w': 'week',
}

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

The unit `1/` represents the reciprocal of the previous unit.

  Examples:

  # Convert column c from feet to meters:
  $ psv in a.csv // unit c_in_meters=c:ft:m // md

  # Convert Haile Gebrselassie's times to minutes per mile:
  $ psv in gebrselassie.csv // coerce seconds=time:seconds // unit seconds:s meters=distance:m // eval 'return {"m_per_s": meters / seconds}' // unit min_per_mile=m_per_s:mile/min:1/ // cut event,distance,time,min_per_mile // md

  '''
  def xform(self, inp, _env):
    define_units(UNITS, UNIT_ALIASES) # ??? DO THIS ONCE!
    conversions = parse_conversions(inp, self.args)
    out = inp.copy()
    for out_col, inp_col, out_units in conversions:
      out[out_col] = self.convert_col(out, inp_col, out_units)
    return out

  def convert_col(self, out, inp_col: str, out_units: List[str]):
    seq = out[inp_col]
    if not out_units:
      seq = self.parse_seq_unit(seq)
    else:
      for out_unit in out_units:
        out_unit = re.sub(r'-', ' ', out_unit)
        seq = self.convert_seq_unit(seq, out_unit)
    return seq

  def parse_seq_unit(self, seq):
    def convert(val):
      if isinstance(val, str):
        return u.Unit(val)
      return val
    seq = seq.apply(convert)
    return seq

  def convert_seq_unit(self, seq, out_unit: str):
    if out_unit == '1/':
      return 1 / seq
    unit = u.Unit(out_unit)
    def convert(val):
      if isinstance(val, (float, int)):
        return val * unit
      if isinstance(val, str):
        return u.Unit(val).to(unit) * unit
      return val.to(unit)
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
