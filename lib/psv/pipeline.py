from typing import Any, List
import shlex
import pandas as pd
from devdriven.util import shorten_string, get_safe
from devdriven.cli.macro import MacroExpander
from .content import Content
from . import command, io

CommandLine = List[str | List]
CommandList = List[List[str]]


class Parser:
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
            if arg == "{{":
                depth += 1
                if recur:
                    stack.append(cmd)
                    cmd = []
                else:
                    cmd.append(arg)
            elif arg == "}}":
                depth -= 1
                if depth < 0:
                    break
                if recur:
                    stack[-1].append(cmd)
                    cmd = stack.pop()
                else:
                    cmd.append(arg)
            elif arg == "//":
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
        self.commands = self.expand_macros(argv)
        self.xforms = list(map(self.make_xform, self.commands))
        return self

    def expand_macros(self, argv: List[str]) -> CommandList:
        # ??? works fine:
        # pylint: disable-next=no-member
        macros = self.main.config.opt("macro", {})
        result: CommandList = []
        prev = Parser().parse(argv)
        while result != prev:
            prev = result
            result = []
            commands = Parser().parse(argv)
            for cmd in commands:
                expansion = MacroExpander(macros=macros).expand(cmd)
                result.extend(Parser().parse(expansion))
        return result

    def prepare_io(self):
        if self.xforms:
            if not isinstance(self.xforms[0], io.IoIn):
                in_cmd = io.IoIn()
                self.xforms.insert(0, in_cmd)
            if not isinstance(self.xforms[-1], io.IoOut):
                out_cmd = io.IoOut()
                self.xforms.append(out_cmd)
        return self

    def xform(self, inp, env):
        assert self.main
        history = env["history"]
        xform_output = xform_input = inp
        i = 0
        for xform in self.xforms:
            xform.main = self.main
            current = [describe_datum(xform), None, None, None]
            history.append(current)
            xform_input = xform_output
            try:
                env["xform"].update(
                    {
                        "first": get_safe(self.xforms, 0),
                        "last": get_safe(self.xforms, -1),
                        "prev": get_safe(self.xforms, i - 1),
                        "next": get_safe(self.xforms, i + 1),
                        "current": current,
                    }
                )
                xform_output = xform.xform(xform_input, env)
            # pylint: disable-next=broad-except
            except Exception as exc:
                self.log("error", "%s", f"{exc}")
                raise
            current[1] = describe_datum(xform_output)
            current[2] = env["Content-Type"]
            current[3] = env["Content-Encoding"]
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
        datum = f"[{len(datum)}]"
    return f"<< {type_name}: {shorten_string(str(datum), 40)} >>"
