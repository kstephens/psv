from devdriven.html import Table
from .command import section, command
from .formats import FormatOut

section("Format", 20)


@command
class HtmlOut(FormatOut):
    """
      html-out - Generate HTML.

      Aliases: html-, html

      --simple, -S         |  Minimal format.
      --title=NAME         |  Set `<title>` and add a `<div>` at the top.
      --parent-link, -P    |  Add `..` parent link to title `<div>`.  Default: False.
      --header, -h         |  Add table header.  Default: True.
      --filtering, -f      |  Add filtering UI.
      --filtering-tooltip  |  Add filtering tooltip.
      --render-link, -L    |  Render http and ftp links.
      --sorting, -s        |  Add sorting support.
      --row-index, -i      |  Add row index to first column.  Default: False.
      --stats              |  Add basic stats to the title `<div>`.
      --table-only, -T     |  Render only a `<table>`.
      --styled             |  Add style.  Default: True.

      :suffixes: .html,.htm

      Examples:

    $ psv in a.csv // html // o a.html
    $ w3m -dump a.html

    $ psv in users.txt // -table --fs=":" // html --title=users.txt // o users-with-title.html
    $ w3m -dump users-with-title.html

    $ psv in users.txt // -table --fs=":" // html --no-header // o users-no-header.html
    $ w3m -dump users-no-header.html

    $ psv in users.txt // -table --fs=":" // html -fs // o users-with-fs.html
    $ w3m -dump users-with-fs.html

    """

    def format_out(self, inp, _env, writeable):
        columns = inp.columns
        rows = inp.to_dict(orient="records")
        column_opts = {}
        for col in columns:
            col_opts = column_opts[col] = {}
            dtype = inp[col].dtype
            if dtype.kind in ("i", "f"):
                col_opts.update(
                    {
                        "numeric": True,
                        "sort_method": "number",
                        "type": dtype.name,
                    }
                )
            if dtype.kind in ("O"):
                type_name = infer_type_name(inp, col)
                col_opts.update({"type": type_name})
                if type_name == "IPv4Address":
                    col_opts.update({"sort_method": "dotsep"})
                # ic((col, dtype, dtype.kind, col_opts))
        opts = {k.replace("-", "_"): v for k, v in self.opts.items()}
        options = {
            "columns": column_opts,
            # 'simple': True,
            "styled": True,
            "header": True,
            # 'table_only': True,
            # 'row_ind': True,
        } | opts
        table = Table(
            columns=columns,
            rows=rows,
            options=options,
            output=writeable,
        )
        table.render()


def infer_type_name(inp, col):
    if inp.shape[0] > 0:
        return type(inp.iloc[0][col]).__name__
    return None
