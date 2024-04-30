# psv

psv - Pandas Separated Values

- Copyright 2021-2024 Kurt Stephens
- git@kurtstephens.com

`psv` is a command-line that manipulates tabular data in multiple formats.
Its design is influenced by the `Unix Principle` of "small tools connected by pipes".

# Features

`psv` can read and write multiple formats of data: CSV, TSV, Markdown, HTML, Pandas pickles.

The string `//` is used to link commands in a pipeline.

# Configuration

`psv` reads configuration from `~/.psv/config.yml` or `$PSV_CONFIG_FILE`.

## Macros

Macro commands are defined in `config.yml`.
Argument substitution is similar to a Unix shell: `$1`, `$@`, etc.

```
# ~/.psv/config.yml:
macro:
  html-full: 'html- --row-index --render-links --style --sorting --filtering --filtering-tooltip "$@"'

```
