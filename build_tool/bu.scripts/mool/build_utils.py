"""Utilities for build project."""

import logging
import os
import subprocess
import sys

import mool.jar_merger as jm
import mool.shared_utils as su
import mool.rule_builder as rb


BUILD_COMMAND = 'do_build'
CLEAN_COMMAND = 'do_clean'
SHOW_ERRORS = True
TEST_COMMAND = 'do_test'
TEST_CHANGES_COMMAND = 'do_test_changes'


USAGE_TEXT = """
Build utiilty tool with rules driven by BLD files.

# To clean working directories.
    $ bu do_clean
    Cleaning directories: ${BUILD_OUT_DIR}, ${BUILD_WORK_DIR}

    # To build.
    $ bu do_build mool.src.main.java.some.work.ProtoSampleMain
    --> Emitting java_bin at ${BUILD_OUT_DIR}/.../ProtoSampleMain.jar

    # To build and run tests.
    $ bu do_test mool.cc.common.some_lib_test
    --> Running test mool.cc.common.some_lib_test

    # To build and run all "submit queue" tests (that have been defined by
    # SUBMITQ files placed appropriately under code root), create a change log
    # file with a list of changed source code files and execute:
    $ bu do_test_changes /change/log/file
    --> Running mool.cc.test1
    --> Running mool.src.test2
    --> ...
"""

ERROR_TEXT = 'ERROR! ERROR! ERROR! ERROR! ERROR!'


class Error(Exception):
  """The Error class for this module."""


def _print_usage():
  """Print usage text if needed.

  Unit tests try out many invalid combinations. There is no need to generate
  verbose test output for such scenarios.
  """
  if not su.TEST_MODE_EXECUTION:
    print USAGE_TEXT


def _clean_temp_dirs():
  """Clean the output directory."""
  logging.info('Cleaning output and working directories: {}, {}'.format(
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
    logging.info('No changes covered by SUBMITQ files or BLD files.')
  if su.SUBMITQ_DEBUG_MODE:
    print '\n'.join(affected_rules)
    affected_rules = []
  return affected_rules


def _apply_rules_internal(rules_list, dependency_dict):
  """Internal implementation of apply_rules."""
  if 1 < len(rules_list) and BUILD_COMMAND == rules_list[0]:
    return rb.RuleBuilder(rules_list[1:]).do_builds(False, dependency_dict)

  if 1 < len(rules_list) and TEST_COMMAND == rules_list[0]:
    return rb.RuleBuilder(rules_list[1:]).do_builds(True, dependency_dict)

  if 2 == len(rules_list) and TEST_CHANGES_COMMAND == rules_list[0]:
    affected_rules = _get_affected_rules(rules_list[1])
    if not affected_rules:
      return 0
    new_rules_list = [TEST_COMMAND]
    new_rules_list.extend(affected_rules)
    return _apply_rules_internal(new_rules_list, dependency_dict)
  _print_usage()
  raise Error('Unexpected command.')


def apply_rules(rules_list, dependency_dict):
  """Apply build rules from a list."""
  if not rules_list:
    _print_usage()
    return 0
  lock_file_object = None
  try:
    if 1 == len(rules_list) and CLEAN_COMMAND == rules_list[0]:
      return _clean_temp_dirs()
    lock_file_object = su.lock_working_dir()
    return _apply_rules_internal(rules_list, dependency_dict)
  except subprocess.CalledProcessError as error_obj:
    # Handle called-command errors in a graceful way. This is the most common
    # scenario from this module as developers make continuous changes in their
    # code.
    logging.error(ERROR_TEXT)
    logging.error('Current directory: %s', su.log_normalize(os.getcwd()))
    error_cmd = [su.log_normalize(x) for x in error_obj.cmd]
    logging.error(' '.join(error_cmd))
    return 1
  except jm.Error as error_obj:
    logging.error(ERROR_TEXT)
    logging.error(str(error_obj))
    return 1
  except:
    if SHOW_ERRORS:
      logging.error('Error: {}'.format(sys.exc_info()))
    raise
  finally:
    su.release_working_dir(lock_file_object)


def do_main(rules_list):
  """Apply build rules from a list."""
  logging.basicConfig(format='%(message)s', level=logging.INFO)
  result = apply_rules(rules_list, {})
  logging.debug('Returning %s', str(result))
  return result
