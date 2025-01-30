import re
import pandas as pd
from .command import section, command, Command

section("I/O", 10)


class SQLCommand(Command):
    def make_engine(self, url: str):
        # pylint: disable-next=import-outside-toplevel
        import sqlalchemy

        if config_vars := self.main.config.opt("variable"):

            def fetch(match):
                return str(config_vars.get(match[1], ""))

            url = re.sub(r"\{\{(\S+)\}\}", fetch, url)
        return sqlalchemy.create_engine(url)


@command
class SQLIn(SQLCommand):
    """
      -sql - Read from a SQL database.

    Arguments:

      TABLE-NAME-or-SQL-QUERY    |  The name of a table or a SQL query.
      CONNECTION-URL             |  The database connection URL in sqlachmemy format.
      --columns=COL,...          |  Columns to read from table.  Default: all columns.
      --parse-dateslist=COL,...  |  List of column names to parse as dates.

    Examples:

    # Convert CSV to sqlite table:
    $ psv in gebrselassie.csv // sql- gebrselassie sqlite:////tmp/geb.db

    # Format sqlite table as Markdown:
    $ psv -sql gebrselassie sqlite:////tmp/geb.db // md

    # Read specific columns:
    $ psv -sql --columns=distance,time gebrselassie sqlite:////tmp/geb.db

    # Query database:
    $ psv -sql 'SELECT * FROM gebrselassie WHERE time > "00:07:"' sqlite:////tmp/geb.db // sort time

    """

    def xform(self, _inp, _env):
        opts = {} | parse_opts(self.opts)
        # ic(opts)
        url = self.args[-1]
        engine = self.make_engine(url)
        sql_or_table = " ".join(self.args[:-1]).strip()
        if re.match(
            r"^(?:(?P<schema>[_a-zA-Z][_a-zA-Z0-9]*)\.)?(?P<table>[_a-zA-Z][_a-zA-Z0-9]*)$",
            sql_or_table,
        ):
            out = pd.read_sql_table(sql_or_table, engine, **opts)
        else:
            out = pd.read_sql_query(sql_or_table, engine, **opts)
        # ic(out)
        return out


@command
class SQLOut(SQLCommand):
    """
      sql- - Write to SQL database.

      DST-TABLE           |  Destination table name.
      CONNECTION-URL      |  The database connection URL in sqlachmemy format.
      --if-exists=ACTION  |  Action to take if table exists: `fail’, ‘replace’, ‘append’.  Default: `replace`.

    Examples:

    # Convert CSV to Sqlite table:
    $ psv in gebrselassie.csv // sql- gebrselassie 'sqlite:////tmp/geb.db'

    # Query Sqlite:
    $ sqlite3 -header -cmd "SELECT * FROM gebrselassie WHERE time > '00:07:'" /tmp/geb.db </dev/null

    """

    def xform(self, inp, _env):
        # ic(self.opts)
        # ic(self.args)
        table_name = self.args[0]
        url = self.args[1]
        engine = self.make_engine(url)
        opts = {
            "if_exists": "replace",
            "chunksize": 1000,
            "method": "multi",
            "index": False,
        } | parse_opts(self.opts)
        # ic(opts)
        rows_written = inp.to_sql(table_name, engine, **opts)
        out = pd.DataFrame(data={"rows_written": [rows_written]})
        return out


def parse_opts(opts):
    result = opts.copy()

    def split_array(name):
        if val := result.get(name, None):
            result[name] = re.split(r"\s+|\s*,\s*", val)

    split_array("columns")
    split_array("index_col")
    split_array("parse_dateslist")
    # ic(result)
    return result
