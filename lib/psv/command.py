from typing import Any, List, Type
import re
import devdriven.cli.command as cmd
from devdriven.cli.descriptor import Descriptor
from devdriven.cli.application import app
from devdriven.cli.types import Argv

# from devdriven.cli.macro import MacroExpander
from devdriven.mime import short_and_long_suffix

Input = Any


class Command(cmd.Command):
    def __call__(self, *args):
        return self.xform(*args)

    def xform(self, inp: Input, _env: dict) -> Any:
        return inp

    def make_xform(self, argv: Argv):  # -> Self:
        return main_make_xform(self.main, argv[0], argv[1:]) or Exception(
            f"unknown command {argv[0]!r}"
        )

    def opt_name_key(self, name: str) -> str:
        return self.command_descriptor().options.opt_name_normalize(name) or name


def main_make_xform(main, klass_or_name: str | Type, argv: Argv) -> Command | None:
    assert main
    # if isinstance(klass_or_name, str):
    #   macros = main.config.opt('macro', {})
    #   cmd_and_args = [klass_or_name, *argv]
    #   expansion = MacroExpander(macros=macros).expand(cmd_and_args)
    #   klass_or_name, *argv = expansion
    if desc := app.descriptor(klass_or_name):
        xform = desc.klass()
        xform.main = main
        xform.name = desc.name
        xform.parse_argv(argv)
        return xform
    main.fatal(f'psv: unknown command {klass_or_name!r} : see {"psv help -s"!r}.')
    return None


def find_format(path: str, klass: Type) -> Type | None:
    short_suffix, long_suffix = short_and_long_suffix(path)
    valid_descs = [dsc for dsc in app.descriptors if issubclass(dsc.klass, klass)]
    for dsc in valid_descs:
        if long_suffix in suffix_list(dsc):
            return dsc.klass
    for dsc in valid_descs:
        if short_suffix in suffix_list(dsc):
            return dsc.klass
    return None


def suffixes(dsc: Descriptor) -> str | None:
    return dsc.metadata.get("suffixes")


def suffix_list(dsc: Descriptor) -> List[str]:
    meta = dsc.metadata
    if not (result := meta.get("suffix_list")):
        sufs = suffixes(dsc)
        meta["suffix_list"] = result = (
            [x.strip() for x in re.split(r"\s*,\s*", sufs)] if sufs else []
        )
    return result


def preferred_suffix(dsc: Descriptor) -> str | None:
    suf = suffix_list(dsc)
    return suf[0] if suf else None


def section(name: str, order: int, *args):
    return app.begin_section(name, order, *args)


# Decorator
def command(klass):
    app.synopsis_prefix = ["psv"]
    return app.command(klass)
