from typing import Any, Union, List, Callable
import shlex
import pandas as pd
from devdriven.util import shorten_string, get_safe
from .content import Content
from . import command

CommandLine = List[Union[str, List]]

class Parser():
  def parse(self, argv: List[str], recur: bool = False) -> List[List]:
    cmds: List[Any] = []
    cmd: List[Any] = []
    stack = [cmds]
    depth = 0

    def flush():
      nonlocal cmd
      if cmd:
        stack[-1].append(cmd)
        cmd = []

    for arg in argv:
      if arg == '{{':
        depth += 1
        if recur:
          stack.append(cmd)
          cmd = []
        else:
          cmd.append(arg)
      elif arg == '}}':
        depth -= 1
        if depth < 0:
          break
        if recur:
          stack[-1].append(cmd)
          cmd = stack.pop()
        else:
          cmd.append(arg)
      elif arg == '//':
        if recur:
          flush()
        elif depth > 0:
          cmd.append(arg)
        else:
          flush()
      else:
        cmd.append(arg)
    if depth != 0:
      raise Exception("unbalanced {{ }} in {argv!r}")
    flush()
    return cmds


class Pipeline(command.Command):
  def __init__(self, *args):
    super().__init__(*args)
    self.xforms = []
    self.commands = []

  def parse_argv(self, argv: List[str]):
    self.commands = Parser().parse(argv)
    self.xforms = list(map(self.make_xform, self.commands))
    return self

  def xform(self, inp, env):
    history = env['history']
    xform_output = xform_input = inp
    i = 0
    for xform in self.xforms:
      current = [describe_datum(xform), None, None, None]
      history.append(current)
      xform_input = xform_output
      try:
        env['xform'].update({
          'first': get_safe(self.xforms, 0),
          'last': get_safe(self.xforms, -1),
          'prev': get_safe(self.xforms, i - 1),
          'next': get_safe(self.xforms, i + 1),
          'current': current,
        })
        xform_output = xform.xform(xform_input, env)
      # pylint: disable-next=broad-except
      except Exception as exc:
        self.log('error', '%s', f'{exc}')
        raise
      current[1] = describe_datum(xform_output)
      current[2] = env['Content-Type']
      current[3] = env['Content-Encoding']
    return xform_output

def describe_datum(datum):
  type_name = datum.__class__.__name__
  if isinstance(datum, command.Command):
    type_name = datum.__class__.__name__
    datum = shlex.join([datum.name] + datum.argv)
  elif isinstance(datum, pd.DataFrame):
    datum = datum.shape
  elif isinstance(datum, Content):
    datum = datum.url
  elif isinstance(datum, (bytes, list, dict)):
    datum = f'[{len(datum)}]'
  return f"<< {type_name}: {shorten_string(str(datum), 40)} >>"
