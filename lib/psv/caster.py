from typing import List, Optional
import re
import ipaddress
import socket
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy

# from devdriven import lazy_import
# import dateparser  # type: ignore

# dateparser = None

NS_PER_SEC = 1000 * 1000 * 1000

TYPES = [
    "str",
    "numeric",
    "int",
    "float",
    "unix_epoch",
    "datetime",
    "timedelta",
    "seconds",
    "ipaddress",
    "hostname",
]

TYPE_ALIASES = {
    "string": "str",
    "n": "numeric",
    "integer": "int",
    "i": "int",
    "f": "float",
    "s": "seconds",
    "sec": "seconds",
    "td": "timedelta",
    "dt": "datetime",
    "ip": "ipaddress",
    "ipaddr": "ipaddress",
    "epoch": "unix_epoch",
    "unix": "unix_epoch",
    # pandas seq.dtype.name:
    "int32": "int",
    "int64": "int",
    "float8": "float",
    "float64": "float",
    "timedelta64": "timedelta",
    "datetime64": "datetime",
}


class Caster:
    type_aliases: dict = {}
    opts: dict = {}

    def __init__(self, type_aliases=None, opts=None):
        self.type_aliases = type_aliases or {}
        self.opts = opts or {}
        self.to_ipaddress = ipaddress_caster()
        self.to_hostname = hostname_caster()
        # dateparser = lazy_import.load('dateparser')

    def cast_to(self, val, out_type: str, inp_type: Optional[str] = None):
        # pylint: disable-next=not-callable
        return self.caster(out_type)(val, inp_type or type(val).__name__)

    def caster(self, out_type: str):
        cast_type = self.type_aliases.get(out_type, out_type)
        if fun := getattr(self, f"_cast_to_{cast_type}", None):
            return fun
        raise Exception(f"unknown cast for type {out_type!r}")

    def _cast_to_str(self, val, _inp_type: str):
        return str(val)

    def _cast_to_numeric(self, val, _inp_type: str):
        return cast_float(val) or cast_int(val)

    def _cast_to_int(self, val, _inp_type: str):
        return cast_int(val)

    def _cast_to_float(self, val, _inp_type: str):
        return cast_float(val)

    def _cast_to_unix_epoch(self, val, inp_type: str):
        if inp_type in NUMERIC:
            return val
        if inp_type.startswith("datetime"):
            return val.timestamp()
        if inp_type.startswith("timedelta"):
            return val.total_seconds()
        return val

    def _cast_to_datetime(self, val, inp_type: str):
        if inp_type.startswith("datetime"):
            return val
        if inp_type in NUMERIC:
            return datetime.fromtimestamp(val)
        if inp_type in OTHER:
            return parse_datetime64(val)
        return val

    def _cast_to_timedelta(self, val, inp_type: str):
        if inp_type.startswith("timedelta"):
            return val
        if inp_type in NUMERIC:
            return timedelta(seconds=val)
        if inp_type.startswith("datetime"):
            return val.timestamp()
        return val

    def _cast_to_seconds(self, val, inp_type: str):
        if inp_type in NUMERIC:
            return val
        if inp_type.startswith("datetime"):
            return val.timestamp()
        if inp_type.startswith("timedelta"):
            return val.total_seconds()
        return val

    def _cast_to_ipaddress(self, val, _inp_type: str):
        return self.to_ipaddress(val)

    def _cast_to_hostname(self, val, _inp_type: str):
        return self.to_hostname(val)

    ###########################################################

    def cast_col(self, out, inp_col: str, out_types: List[str]):
        seq = out[inp_col]
        inp_type = seq.dtype.name
        for out_type in out_types:
            out_type = re.sub(r"-", "_", out_type)
            seq = self.cast_seq_type(seq, inp_type, out_type)
            inp_type = seq.dtype.name
        return seq

    def cast_seq(self, seq, out_type: str):
        return self.cast_seq_type(seq, seq.dtype.name, out_type)

    def cast_seq_type(self, seq, inp_type: str, out_type: str):
        # pylint: disable-next=not-callable
        return self.seq_caster(out_type)(seq, inp_type)

    def seq_caster(self, out_type: str):
        cast_type = self.type_aliases.get(out_type, out_type)
        if fun := getattr(self, f"_cast_seq_to_{cast_type}", None):
            return fun
        raise Exception("unknown cast for type {out_type!r}")

    def _cast_seq_to_str(self, seq, _inp_type: str):
        return pd.Series(seq.astype(str))

    def _cast_seq_to_numeric(self, seq, _inp_type: str):
        return pd.to_numeric(seq, errors="coerce")

    def _cast_seq_to_int(self, seq, _inp_type: str):
        return pd.to_numeric(seq, downcast="integer", errors="coerce")

    def _cast_seq_to_float(self, seq, _inp_type: str):
        return pd.to_numeric(seq, downcast="float", errors="coerce")

    def _cast_seq_to_unix_epoch(self, seq, inp_type: str):
        if inp_type in NUMERIC:
            return seq
        seq = self.cast_seq(seq, "datetime")
        # ic(seq.dtype.name)
        if seq.dtype.name.startswith("datetime64[ns"):
            seq = seq.astype("int64").astype("float64") / NS_PER_SEC
        return seq

    def _cast_seq_to_datetime(self, seq, inp_type: str):
        if inp_type.startswith("datetime"):
            return seq
        if inp_type in NUMERIC:
            return pd.to_datetime(
                seq, unit="s", origin="unix", errors="ignore", cache=True
            )
        if inp_type in OTHER:
            return pd.Series(seq.apply(parse_datetime64))
        return pd.to_datetime(
            seq,
            errors="ignore",
            cache=True,
            format="mixed",
            # UserWarning: The argument 'infer_datetime_format' is deprecated and will be removed in a future version.
            # A strict version of it is now the default,
            # see https://pandas.pydata.org/pdeps/0004-consistent-to-datetime-parsing.html.
            # You can safely remove this argument.
            # infer_datetime_format=True,
            utc=self.opts.get("utc", True),
        )

    def _cast_seq_to_timedelta(self, seq, inp_type: str):
        if inp_type.startswith("timedelta"):
            return seq
        if inp_type in NUMERIC:
            return pd.to_timedelta(seq, unit="s", errors="ignore")  # type: ignore[call-overload]
        return pd.to_timedelta(seq, errors="ignore")  # type: ignore[call-overload]

    def _cast_seq_to_seconds(self, seq, _inp_type: str):
        if not seq.dtype.name.startswith("datetime"):
            seq = pd.to_timedelta(seq)  # , errors='ignore'
        seq = seq.dt.total_seconds()
        return seq

    def _cast_seq_to_ipaddress(self, seq, _inp_type: str):
        return pd.Series(seq.apply(self.to_ipaddress))

    def _cast_seq_to_hostname(self, seq, _inp_type: str):
        return pd.Series(seq.apply(self.to_hostname))


###########################################################


OTHER = ("str", "string", "object")
NUMERIC = ("float", "float8", "float64", "int", "int16", "int32", "int64")


def cast_int(val):
    try:
        return int(val)
    except ValueError:
        return None


def cast_float(val):
    try:
        return float(val)
    except ValueError:
        return None


def parse_datetime64(val):
    try:
        # nginx: time_local "27/Jun/2024:17:15:53 -0500"
        if result := datetime.strptime(str(val), "%d/%b/%Y:%H:%M:%S %z"):
            return numpy.datetime64(result)
    except ValueError:
        pass
    try:
        # pylint: disable-next=import-outside-toplevel
        import dateparser

        return numpy.datetime64(dateparser.parse(str(val)))
    # pylint: disable-next=broad-except
    except Exception:
        return val


def ipaddress_caster():
    cache = {}

    def to_ipaddr(val):
        try:
            if isinstance(val, str):
                if val in cache:
                    return cache[val]
                cache[val] = ipaddr = ipaddress.ip_address(val)
                return ipaddr
            return None
        except ValueError:
            return None

    return to_ipaddr


def hostname_caster():
    cache = {}

    def to_hostname(val):
        try:
            val = str(val)
            if val in cache:
                return cache[val]
            record = socket.gethostbyaddr(val)
            result = cache[val] = record[0]
            return result
        # pylint: disable-next=broad-except
        except Exception:
            return None

    return to_hostname


if __name__ == "__main__":

    def main():
        caster = Caster()
        in_type = sys.argv[1]
        out_type = sys.argv[2]

        def parse_input(val):
            return caster.cast_to(val, in_type) or val

        while line := sys.stdin.readline():
            x = caster.cast_to(parse_input(line.strip()), out_type)
            sys.stdout.write(f"{type(x).__name__}\t{x!r}\t{str(x)!r}\n")

    main()
