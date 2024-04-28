import pandas as pd
# from icecream import ic
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.sql import table, column, select
from sqlalchemy.sql.expression import Select, TextClause
from sqlalchemy.dialects import postgresql
from pandas.io.sql import SQLTable
from .command import section, command
from .formats import FormatOut

# See:
# * https://github.com/pandas-dev/pandas/blob/main/pandas/io/sql.py
# * https://stackoverflow.com/a/23835766/1141958
# * https://stackoverflow.com/a/75679464/1141958


section('Format', 20)

@command
class SQLOut(FormatOut):
  '''
  sql- - Write SQL.
  alias: sql

  --action=ACTION,...     |  Actions to perform: create, trunc, TODO.
  --table=TABLE           |  Table name.  Default: `__table__`.

# Convert TSV to SQL schema:
$ psv in a.tsv // sql

  :suffixes: .sql
  '''
  def format_out(self, inp, env, writeable):
    # https://stackoverflow.com/a/31075679/1141958
    # https://stackoverflow.com/a/51294670/1141958
    actions = self.opt('action', 'create').strip().split(',')
    # See: https://www.rfc-editor.org/rfc/rfc6922.html
    env['Content-Type'] = 'application/sql'
    for action in actions:
      func = getattr(self, f'action_{action}')
      sql = func(inp, env)
      writeable.write(sql)

  def table_name(self):
    return self.opt('table', '__table__')

  def table_object(self, inp):
    columns = []
    for col in inp.columns:
      columns.append(Column(col))
    tab = Table(self.table_name(),
                  MetaData(),
                  *columns
                  )
    return tab

  def action_create(self, inp, _env):
    if not self.opt('index', False):
      inp = inp.reset_index(drop=True)
    # inp.drop(labels=['index'], axis=1, errors='ignore', inplace=True)
    # inp.drop(labels=['index'], axis=0, errors='ignore', inplace=True)
    return pd.io.sql.get_schema(inp, name=self.table_name())

  def action_insert(self, inp, _env):
    return '-- INSERT'

  def action_trunc(self, inp, _env):
    return '-- TRUNC'

'''
# Generating a SELECT stmt:
from sqlalchemy.sql import table, column, select
t = table('t', column('x'))
s = select([t]).where(t.c.x == 5)
print(s.compile(compile_kwargs={"literal_binds": True}))
'''
