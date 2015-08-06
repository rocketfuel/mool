"""Utilities for build project."""

import logging
import os
import subprocess
import sys

import extensions.extensions_main as em
import mool.core_cmds as core_cmds
import mool.shared_utils as su

LOG = logging.getLogger()

ERROR_TEXT = 'ERROR! ERROR! ERROR! ERROR! ERROR!'
SHOW_ERRORS = True


class Error(su.Error):
  """The Error class for this module."""


def _configure_logging(console=True):
  """Setup logging. Enable console logging by default."""
  level = logging.INFO
  log_format = '%(message)s'
  if os.environ.get('DEBUG_MODE', None):
    level = logging.DEBUG
    log_format = '[%(levelname)s] %(name)s: ' + log_format
  LOG.setLevel(level)
  if console:
    console_handle = logging.StreamHandler(sys.stderr)
    console_handle.setLevel(level)
    console_handle.setFormatter(logging.Formatter(log_format))
    LOG.addHandler(console_handle)


def _check_working_dirs():
  """Ensure that out and work directories exist."""
  su.createdir(su.BUILD_OUT_DIR)
  su.createdir(su.BUILD_WORK_DIR)


def _generate_help_message():
  """Generates a help message from core and extension commands."""
  def _format_line(cmd, text):
    """Align command and help text."""
    return '%20s : %s' % (cmd, text)

  header = "Build utility tool with rules driven by BLD files."
  footer = "Run 'bu <command> --help' for more help on that command."
  core_help = []
  for key in sorted(core_cmds.CORE_COMMANDS.keys()):
    core_help.append(_format_line(key, core_cmds.CORE_COMMANDS[key][1]))
  ext_help = []
  for key in sorted(em.EXTENSION_COMMANDS.keys()):
    ext_help.append(_format_line(key, em.EXTENSION_COMMANDS[key][1]))

  message = '{}\n\nCore commands:\n{}\n\nExtensions:\n{}\n\n{}'.format(
      header, '\n'.join(core_help), '\n'.join(ext_help), footer)
  return message


def _get_cmd_handler(cmd_line):
  """Returns appropriate handler for given command line."""
  if not cmd_line or cmd_line[0] in ['-h', '--help', 'help']:
    if SHOW_ERRORS:
      print _generate_help_message()
    return (None, 0)

  cmd = cmd_line[0]
  if cmd in core_cmds.CORE_COMMANDS:
    return (core_cmds.generic_core_cmd_handler, 0)
  elif cmd in em.EXTENSION_COMMANDS:
    return (em.generic_extension_handler, 0)
  else:
    if SHOW_ERRORS:
      print 'Error: Unknown command "{}". Use "bu help" for more.'.format(cmd)
    return (None, 1)


def apply_rules(cmd_line, dependency_dict):
  """Takes the command line arguments and appropriately calls the handler
  function of a command, else prints the help message."""
  handler, status = _get_cmd_handler(cmd_line)
  if not handler:
    return (status,)

  try:
    _check_working_dirs()
    return handler(cmd_line, dependency_dict)
  except subprocess.CalledProcessError as error_obj:
    # Handle called-command errors in a graceful way. This is the most common
    # scenario from this module as developers make continuous changes in their
    # code.
    LOG.error(ERROR_TEXT)
    LOG.error('Current directory: %s', su.log_normalize(os.getcwd()))
    error_cmd = [su.log_normalize(x) for x in error_obj.cmd]
    LOG.error(' '.join(error_cmd))
    return (1,)
  except su.Error as error_obj:
    LOG.error(ERROR_TEXT)
    LOG.error('ERROR: %s', su.log_normalize(str(error_obj)))
    return (1,)


def do_main(rules_list):
  """Apply build rules from a list."""
  _configure_logging()
  lock_file_object = None
  result = None
  try:
    _check_working_dirs()
    lock_file_object = su.lock_working_dir()
    result = apply_rules(rules_list, {})
  finally:
    su.release_working_dir(lock_file_object)
  if not isinstance(result, tuple):
    LOG.error('Expecting a tuple return value!')
  ret_code = result[0]
  LOG.debug('Returning %s', str(ret_code))
  return ret_code
