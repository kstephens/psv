import re
import sys

def fix_line(line):
  def replace(m):
    return f'{m[1]}...{m[3]}'
  return re.sub(r'( *"(?:now|cwd)": *")(:?[^"]*)(")\s*', replace, line)
  # line = re.sub(r'\s+$', '\n', line)
  # return line


if __name__ == '__main__':
  lines = sys.stdin.readlines()
  lines = [fix_line(line) for line in lines]
  sys.stdout.write(''.join(lines))
