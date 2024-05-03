from .pipeline import Parser

def test_parse():
  def parse(argv):
    return Parser().parse(argv)
  assert parse([]) == []
  assert parse(['a']) == [['a']]
  assert parse(['a', 'b']) == [['a', 'b']]
  assert parse(['a', 'b', '//', 'c']) == [['a', 'b'], ['c']]
  assert parse(['//', 'c']) == [['c']]
  assert parse(['a', '{{', 'b', '//', 'c', '}}', 'd', '//', 'e', 'f']) == [['a', '{{', 'b', '//', 'c', '}}', 'd'], ['e', 'f']]

def test_parse_recur():
  def parse(input):
      return Parser().parse(input, recur=True)
  assert parse([]) == []
  assert parse(['a']) == [['a']]
  assert parse(['a', '//', 'b', 'c', '//']) == \
    [['a'], ['b', 'c']]
  assert parse(['a', '//', 'b', '{{', 1, 2, '}}', 'c', '//', 'd']) == \
    [['a'], ['b', [1, 2], 'c'], ['d']]
  # Assert exception:
  # scan(['a', '//', 'b', '{{', '}}', 'c'], [['a'], ['b']])
