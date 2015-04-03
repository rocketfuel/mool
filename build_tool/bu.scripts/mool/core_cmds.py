"""Handlers and entry point for mool core commands."""
import logging
import os

import mool.rule_builder as rb
import mool.shared_utils as su

LOG = logging.getLogger()

# Dictionary of all the core commands here.
# <Command Name> : (<Handler Function>, <One line help message>)
BUILD_COMMAND = 'do_build'
CLEAN_COMMAND = 'do_clean'
TEST_COMMAND = 'do_test'
TEST_CHANGES_COMMAND = 'do_test_changes'

CORE_COMMANDS = {
    BUILD_COMMAND: ('_handle_do_build', 'build a list of given rules.'),
    CLEAN_COMMAND: ('_handle_do_clean',
                    'create/clean output and working directories.'),
    TEST_COMMAND: ('_handle_do_test', 'build and test a list of rules.'),
    TEST_CHANGES_COMMAND: ('_handle_do_test_changes',
                           ('builds and runs SUBMITQ rules for a list of '
                            'changed files given in a file.'))
}


class Error(su.Error):
  """The Error class for this module."""


def _clean_temp_dirs():
  """Clean the output directory."""
  LOG.info('Cleaning output and working directories: {}, {}'.format(
      su.log_normalize(su.BUILD_OUT_DIR), su.log_normalize(su.BUILD_WORK_DIR)))
  su.cleandir(su.BUILD_OUT_DIR)
  su.cleandir(su.BUILD_WORK_DIR)
  return 0


def _get_affected_rules(changed_files_list_file):
  """Get list of affected rules from file containing list of changed files."""
  changed_files_list = [
      f.strip() for f in su.read_file(changed_files_list_file).split('\n')
      if f.strip()]
  changed_files_list = [os.path.realpath(f) for f in changed_files_list]
  affected_rules = su.get_affected_rules(changed_files_list)
  if not affected_rules:
    LOG.info('No changes covered by SUBMITQ files or BLD files.')
  if su.SUBMITQ_DEBUG_MODE:
    print '\n'.join(affected_rules)
    affected_rules = []
  return affected_rules


def _handle_do_build(params, dependency_dict):
  """Handler for do_build command."""
  if not params:
    raise Error('bu do_build expects a list of rules to build.')
  builder = rb.RuleBuilder(params)
  ret_code = builder.do_builds(False, dependency_dict)
  return ret_code, builder


def _handle_do_clean(_, ___):
  """Handler for do_clean command."""
  return (_clean_temp_dirs(),)


def _handle_do_test(params, dependency_dict):
  """Handler for do_test command."""
  if not params:
    raise Error('bu do_test expects a list of rules to build.')
  builder = rb.RuleBuilder(params)
  ret_code = builder.do_builds(True, dependency_dict)
  return ret_code, builder


def _handle_do_test_changes(params, dependency_dict):
  """Handler for do_test_changes command."""
  if not params:
    raise Error('bu do_test_changes expects path to a file.')
  affected_rules = _get_affected_rules(params[0])
  if not affected_rules:
    return (0,)
  return _handle_do_test(affected_rules, dependency_dict)


def generic_core_cmd_handler(params, dependency_dict):
  """Entry point for all the core commands."""
  handler = globals()[CORE_COMMANDS[params[0]][0]]
  return handler(params[1:], dependency_dict)
