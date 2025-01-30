import re
import sys


def fix_line(line):
    def replace(m):
        return f"{m[1]}...{m[3]}\n"

    return re.sub(r'( *"(?:now|cwd)": *")(:?[^"]*)("\S*)\s*', replace, line)


if __name__ == "__main__":
    lines = sys.stdin.readlines()
    lines = [fix_line(line) for line in lines]
    sys.stdout.write("".join(lines))
