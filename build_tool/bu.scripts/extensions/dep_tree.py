"""Prints dependency tree of a build rule"""
import argparse

import mool.core_cmds as cc
import mool.shared_utils as su

CHILD_NODE = '|-- '
HAS_PARENT_PAD = '|   '
INDENT_PAD = '    '
LAST_CHILD_NODE = '`-- '

PROHIBITED_KEYS = (su.ALL_RULES_KEY, su.ALL_LIGHT_RULES_KEY)


def _parse_command_line(program_name, cmd_line):
  """Parse command line to generate arguments."""
  parser = argparse.ArgumentParser(prog=program_name)
  parser.add_argument('build_rule', metavar='build_rule',
                      help='Full name build rule to find the dependencies of')
  return parser.parse_args(cmd_line)


def _get_maven_format_str(rule_details):
  """Returns formatted string if the rule is maven build rule."""
  specs = rule_details.get(su.MAVEN_SPECS_KEY, None)
  maven_str = ''
  if not specs:
    return maven_str

  maven_str = ' ({}:{}:{})'.format(
      specs[su.MAVEN_GROUP_ID_KEY],
      specs[su.MAVEN_ARTIFACT_ID_KEY],
      specs[su.MAVEN_VERSION_KEY])
  return maven_str


def _print_tree(builder, top_rule, indent_pads, last=False, compile_dep=False):
  """Prints a formatted dependency tree."""
  rule_details = builder.get_rules_map().get(top_rule)
  maven_str = _get_maven_format_str(rule_details)

  # Format and print details of this rule with proper indentation.
  indent_str = ''.join(indent_pads)
  if any(indent_pads):
    indent_str += CHILD_NODE if not last else LAST_CHILD_NODE
  dep_type = ' (compileDep)' if compile_dep else ''

  print '{}{}{}{}'.format(indent_str, top_rule, maven_str, dep_type)
  rule_deps = []
  rule_deps.extend([(r, False) for r in rule_details[su.DEPS_KEY]])
  rule_deps.extend([(r, True) for r in rule_details[su.COMPILE_DEPS_KEY]])
  if (top_rule, compile_dep) in rule_deps:
    rule_deps.remove((top_rule, compile_dep))
  # First sort by rule name and then by dependency type.
  rule_deps = sorted(rule_deps, key=lambda x: x[0])
  rule_deps = sorted(rule_deps, key=lambda x: x[1])

  # Recursively process all the dependencies of this rule now.
  indent_pads.append(HAS_PARENT_PAD if not last else INDENT_PAD)
  for dep in rule_deps[0:-1]:
    _print_tree(builder, dep[0], indent_pads, False, dep[1])
  if len(rule_deps):
    _print_tree(builder, rule_deps[-1][0], indent_pads, True, rule_deps[-1][1])
  indent_pads.pop()


def main(program_name, cmd_line):
  """Main function to trigger rule building and dependency tree generation."""
  args = _parse_command_line(program_name, cmd_line)

  # We need precisely one rule for processing the dependency tree.
  if any([args.build_rule.endswith(key) for key in PROHIBITED_KEYS]):
    msg = 'Please specify the rule name, cannot use [{}] keys!'.format(
        ', '.join(PROHIBITED_KEYS))
    print msg
    return (1, msg)

  ___, builder = cc.generic_core_cmd_handler(
      [cc.BUILD_COMMAND, args.build_rule], {})
  print '{0} Dependency tree of {1} {0}'.format('=' * 15, args.build_rule)
  _print_tree(builder, args.build_rule, [], True)
  return (0, '')
