"""Mool BLD files are JSON files with comments which need processing before one
can use them as pure JSON. Its even non-trivial to modify it and retain the
comments. This module provides utilities to make the modifications easy."""

from collections import OrderedDict
import json
import re

# TODO: Move the read_build_file function here from mool.shared_utils.
import mool.shared_utils as su
import utils.file_utils as fu

COMMENT_CHAR = '#'
QUOTE_CHAR = '"'
RULE_NAME_KEY = 'name'
RULE_BODY_KEY = 'body'
SORT_ORDER = ['rule_type', 'srcs', 'deps']


def _rule_name(text):
  """Extact a rule's name."""
  parts = re.findall(r'"([^"]*)"', text)
  assert len(parts) == 1, "Unable to parse rule name from: %s" % text
  return parts[0]


def _is_end_of_rule(text):
  """Check if this text represents end of a rule."""
  return (text.startswith('},') or text.startswith('}') or
          text.endswith('},') or text.endswith('}'))


def _strip_rule_body(lines):
  """Remove text belonging to a rule's body from given list of lines."""
  assert len(lines) > 0
  text = lines[0]
  while lines and not _is_end_of_rule(text):
    text = lines.pop(0)
    # If rule body has a dictionary element (for example: maven spec),
    # strip it recursively.
    if text.endswith('{'):
      _strip_rule_body(lines)


def _format_rule(name, json_body):
  """Prettify a single rule per BLD formatting guidelines."""
  sorted_json_body = OrderedDict(sorted(
      json_body.items(),
      key=lambda (k, _): SORT_ORDER.index(k) if k in SORT_ORDER else k))
  json_dump = json.dumps(sorted_json_body, indent=4, separators=(',', ': '))
  return '{}{}{}: {}'.format(QUOTE_CHAR, name, QUOTE_CHAR, json_dump)


def list_to_bld_string(bld_list):
  """Takes a list of comments, new lines and dict(rule) and generates the BLD
  file data."""
  rules = 0
  for item in bld_list:
    if isinstance(item, dict):
      rules += 1

  formatted = []
  processed = 0
  for item in bld_list:
    if not isinstance(item, dict):
      formatted.append(item)
    else:
      processed += 1
      formatted.append('{}{}'.format(_format_rule(item[RULE_NAME_KEY],
                                                  item[RULE_BODY_KEY]),
                       '' if rules == processed else ','))
  formatted = [l.strip('\n') for l in formatted]
  return '{}\n'.format('\n'.join(formatted).rstrip())


def bld_to_list(file_path):
  """Takes a BLD file path and returns an OrderedList of comments, new lines
  and dict(rule) in the file."""
  # Abort quickly if its a bad JSON file.
  bld_as_json = su.read_build_file(file_path)

  # Format each rule one by one. Preserve the comments only outside the body
  # of rule dictionary.
  lines = [l.strip() for l in fu.read_file(file_path).split('\n')]
  formatted = []
  while lines:
    line = lines.pop(0)
    if not line or line.startswith(COMMENT_CHAR):
      formatted.append(line)
    elif line.startswith(QUOTE_CHAR):
      name = _rule_name(line)
      # TODO: Improve it to retain comments inside a BLD rule as well.
      formatted.append({RULE_NAME_KEY: name, RULE_BODY_KEY: bld_as_json[name]})
      # Skip remaining lines of this rule now.
      _strip_rule_body(lines)
    else:
      raise ValueError('Illegal text %s found in file %s.' % (line, file_path))

  # Do a sanity check, formatting shouldn't change build file's semantics.
  temp_file = fu.get_temp_file()
  fu.write_file(temp_file, list_to_bld_string(formatted))
  formatted_bld_as_json = su.read_build_file(temp_file)
  assert formatted_bld_as_json == bld_as_json
  return formatted
