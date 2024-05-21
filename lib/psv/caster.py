from typing import List
import re
import ipaddress
import pandas as pd

NS_PER_SEC = 1000 * 1000 * 1000

class Caster:
  type_aliases: dict = {}
  opts: dict = {}

  def __init__(self, type_aliases=None, opts=None):
    self.type_aliases = (type_aliases or {})
    self.opts = (opts or {})

  def cast_col(self, out, inp_col: str, out_types: List[str]):
    seq = out[inp_col]
    inp_type = seq.dtype.name
    for out_type in out_types:
      out_type = re.sub(r'-', '_', out_type)
      seq = self.cast_seq_type(seq, inp_type, out_type)
      inp_type = seq.dtype.name
    return seq

  def cast_seq(self, seq, out_type: str):
    return self.cast_seq_type(seq, seq.dtype.name, out_type)

  def cast_seq_type(self, seq, inp_type: str, out_type: str):
    return self.seq_caster(out_type)(seq, inp_type)

  def seq_caster(self, out_type: str):
    cast_type = self.type_aliases.get(out_type, out_type)
    if fun := getattr(self, f'_cast_seq_to_{cast_type}', None):
      return fun
    raise Exception("unknown cast for type {out_type!r}")

  def _cast_seq_to_numeric(self, seq, _inp_type: str):
    return pd.to_numeric(seq, errors='coerce')

  def _cast_seq_to_int(self, seq, _inp_type: str):
    return pd.to_numeric(seq, downcast='integer', errors='coerce')

  def _cast_seq_to_float(self, seq, _inp_type: str):
    return pd.to_numeric(seq, downcast='float', errors='coerce')

  def _cast_seq_to_string(self, seq, _inp_type: str):
    return pd.Series(seq.astype(str))

  def _cast_seq_to_unix_epoch(self, seq, inp_type: str):
    if inp_type in ('float', 'int'):
      return seq
    seq = self.cast_seq(seq, 'datetime')
    # ic(seq.dtype.name)
    if seq.dtype.name.startswith('datetime64[ns'):
      seq = seq.astype('int64').astype('float64') / NS_PER_SEC
    return seq

  def _cast_seq_to_datetime64(self, seq, inp_type: str):
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
      utc=self.opts.get('utc', True)
    )

  def _cast_seq_to_timedelta64(self, seq, inp_type: str):
    if inp_type in ('timedelta64'):
      return seq
    if inp_type in ('float', 'int', 'int32', 'int64'):
      return pd.to_timedelta(seq, unit='s', errors='ignore')
    return pd.to_timedelta(seq, errors='ignore')

  def _cast_seq_to_seconds(self, seq, _inp_type: str):
    if not seq.dtype.name.startswith('datetime'):
      seq = pd.to_timedelta(seq) # , errors='ignore'
    seq = seq.dt.total_seconds()
    return seq

  def _cast_seq_to_ipaddress(self, seq, _inp_type: str):
    to_ipaddr = ipaddress_caster()
    return pd.Series(seq.apply(to_ipaddr))

def ipaddress_caster():
  cache = {}
  def to_ipaddr(val):
    try:
      if isinstance(val, str):
        if val in cache:
          return cache[val]
        cache[val] = ipaddr = ipaddress.ip_address(val)
        # ic(type(ipaddr))
        return ipaddr
      return None
    except ValueError:
      return None
  return to_ipaddr
