"""Implement the rules of each Python build utility type."""
import compileall
import logging
import os
import subprocess
import zipfile

import mool.shared_utils as su

MAIN_FILE_NAME = '__main__.py'
INIT_FILE_NAME = '__init__.py'
PY_SHEBANG_HEADER = '#!/usr/bin/env python2.7\n'
SHEBANG_SYMBOL = '#!'

# Thanks to the Python community for making this part significantly simpler
# than the py.test binary generation part. Essentially python2.7 interpreter
# can handle a zip file as a module now.
PY_MODULE_NAME_SEPARATOR = '.'
MAIN_FILE_CONTENTS_FOR_BIN = """
import sys
import {0}
sys.exit({0}.{1}())
"""


MAIN_FILE_CONTENTS_FOR_TEST = """
import os
import shutil
import sys
import subprocess
import zipfile

# Get the full path name.
binary_file_path = os.path.abspath(sys.argv[0])
assert os.path.exists(binary_file_path)

# Get the path to the extraction directory.
zipdir_path = binary_file_path + '.extract'

# Since we cannot guarantee contents of directory if it exists, we need to
# make a fresh start to avoid unpredictable test behavior.
if os.path.exists(zipdir_path):
  shutil.rmtree(zipdir_path)

# Extract python zipped file data to extraction directory.
os.makedirs(zipdir_path)
with zipfile.ZipFile(binary_file_path, 'r') as zipfile_obj:
  zipfile_obj.extractall(zipdir_path)

# Switch path to extracted directory and execute py.test.
os.chdir(zipdir_path)
subprocess.check_call(['py.test', '-s', '.'])
"""


class Error(Exception):
  """Error class for this module."""


def compile_all(params):
  """Compile python code recursively under current directory."""
  assert not params
  compileall.compile_dir('./', quiet=True)


def expand_lib(params):
  """Expand a link library in place."""
  link_lib, is_zipped = params
  tracer = logging.debug
  if is_zipped:
    tracer('Expanding zipped lib at %s', link_lib)
    with zipfile.ZipFile(link_lib, 'r') as zip_obj:
      zip_obj.extractall()
  else:
    tracer('Expanding directory lib at %s', link_lib)
    # Recursively copying a directory to another. We cannot use shutil.copytree
    # as we cannot assume the directory to be new.
    link_lib = link_lib if link_lib.endswith(os.sep) else link_lib + os.sep
    for root, _, files in os.walk(link_lib):
      for file_path in files:
        src_file = os.path.join(root, file_path)
        dst_file = src_file.replace(link_lib, '.' + os.sep)
        tracer('Copying %s to %s', src_file, dst_file)
        subprocess.check_call(su.get_mkdir_command(os.path.dirname(dst_file)))
        subprocess.check_call(['cp', src_file, dst_file])


def _main_file_contents_for_bin(main_class):
  """Get file contents of __main__.py for python binary."""
  parts = main_class.split(PY_MODULE_NAME_SEPARATOR)
  module = PY_MODULE_NAME_SEPARATOR.join(parts[:-1])
  entry_point = parts[-1]
  return MAIN_FILE_CONTENTS_FOR_BIN.format(module, entry_point)


def perform_linking(command_parts):
  """Steps to perform actual python linking."""
  rule_type, main_class, tmp_out_file, out_file = command_parts
  main_file_path = os.path.join('.', MAIN_FILE_NAME)
  if su.PYTHON_BIN_TYPE == rule_type:
    su.write_file(main_file_path, _main_file_contents_for_bin(main_class))
  elif su.PYTHON_TEST_TYPE == rule_type:
    su.write_file(main_file_path, MAIN_FILE_CONTENTS_FOR_TEST)

  with zipfile.ZipFile(tmp_out_file, 'w') as zip_obj:
    for root, _, files in os.walk('.'):
      for file_path in files:
        full_file_path = os.path.join(root, file_path)
        # It is ok to skip raw .py files for py binaries. The directory has
        # been compiled before the linking step. Therefore it is sufficient to
        # ignore the .py files and pick up the .pyc files instead.
        skip_file = (rule_type == su.PYTHON_BIN_TYPE and
                     full_file_path != main_file_path and
                     file_path.endswith('.py'))
        if skip_file:
          continue
        zip_obj.write(full_file_path)

  if su.PYTHON_LIB_TYPE == rule_type:
    subprocess.check_call(['mv', tmp_out_file, out_file])
  elif su.PYTHON_BIN_TYPE == rule_type:
    su.write_file(out_file, PY_SHEBANG_HEADER + su.read_file(tmp_out_file))
    subprocess.check_call(['chmod', '+x', out_file])
  else:
    assert su.PYTHON_TEST_TYPE == rule_type
    su.write_file(out_file, PY_SHEBANG_HEADER + su.read_file(tmp_out_file))
    subprocess.check_call(['chmod', '+x', out_file])


def create_initializers(params):
  """Create initializers recursively under current subdirectory."""
  assert not params
  for root, _unused_dirs, _unused_files in os.walk('.'):
    if root == '.':
      continue
    init_file = os.path.join(root, INIT_FILE_NAME)
    if su.path_exists(init_file):
      continue
    su.write_file(init_file, '')


def coding_guidelines_check(file_list):
  """Check other desired coding guidelines like shebang, file execution
  permission and coding standards not coverted by pylint/pip."""
  for source in file_list:
    line_number = 0
    if os.access(source, os.X_OK):
      raise Error('Disable execution permissions for {}.'.format(source))
    for line in su.read_file(source).split('\n'):
      line_number += 1
      if line_number == 1 and line.startswith(SHEBANG_SYMBOL):
        raise Error('Remove shebang header from {} file.'.format(source))
      if line.endswith('\\'):
        raise Error(('Line continuation not allowed using backslash in file'
                     ' {}:{}').format(source, line_number))


def _get_lint_commands(rule_details):
  """Get lint and other static code check commands from sources."""
  lint_commands = []
  src_files = [su.get_relative_path(rule_details[su.POSSIBLE_PREFIXES_KEY], f)
               for f in rule_details[su.SRCS_KEY]]
  for file_path in src_files:
    if INIT_FILE_NAME == os.path.basename(file_path):
      continue
    lint_commands.append(
        ['pylint', '--rcfile=' + su.PYLINT_RC_FILE, file_path])
    pep8_command = su.PEP8_COMMAND_LINE[:]
    pep8_command.append(file_path)
    lint_commands.append(pep8_command)
  return lint_commands


def _get_all_deps(rule_details, details_map):
  """Get all link libraries for a Python build rule."""
  link_libs = []
  dep_sources = []
  for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
    if rule_symbol == rule_details[su.SYMBOL_KEY]:
      continue
    link_libs.append(details_map[rule_symbol][su.OUT_KEY])
    dep_sources.extend(details_map[rule_symbol][su.SRCS_KEY])
  link_libs = sorted(list(set(link_libs)))
  return link_libs, dep_sources


class PyCommon(object):
  """Common Python handler functions."""
  @classmethod
  def _set_all_dep_paths(cls, rule_details, link_libs, dep_sources):
    """Set all dependency paths list for the rule."""
    all_dep_paths = rule_details[su.SRCS_KEY][:]
    all_dep_paths.extend(link_libs)
    all_dep_paths.extend(dep_sources)
    all_dep_paths.append(rule_details[su.OUT_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(sorted(list(set(all_dep_paths))))

  @classmethod
  def _internal_setup(cls, rule_details, details_map, is_test):
    """Initializing build rule dictionary."""
    su.init_rule_common(rule_details, rule_details[su.NAME_KEY], [su.SRCS_KEY])
    su.set_workdir_child(rule_details, su.WDIR_SRC_KEY, 'code')
    su.set_workdir_child(rule_details, su.WDIR_TARGET_KEY, 'target')
    skip_lint = rule_details.get(su.PYTHON_SKIPLINT_KEY, 'False').lower()
    rule_details[su.PYTHON_SKIPLINT_KEY] = (skip_lint == 'true')
    if is_test:
      rule_details[su.TEST_COMMANDS_KEY] = [[rule_details[su.OUT_KEY]]]
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    link_libs, dep_sources = _get_all_deps(rule_details, details_map)
    cls._set_all_dep_paths(rule_details, link_libs, dep_sources)
    rule_details[su.LINK_LIBS_KEY] = link_libs
    cls._set_link_command(rule_details)

  @classmethod
  def _set_link_command(cls, rule_details):
    """Set Python link command."""
    main_class = rule_details.get(su.MAIN_METHOD_KEY,
                                  su.PYTHON_FAKE_MAIN_METHOD)
    link_commands = [[su.CHANGE_CURR_DIR, rule_details[su.WDIR_SRC_KEY]]]
    link_libs = rule_details[su.LINK_LIBS_KEY]
    for link_lib in link_libs:
      link_commands.append([su.PYTHON_EXPAND_LIB, link_lib, True])
    if not rule_details[su.PYTHON_SKIPLINT_KEY]:
      link_commands.extend(_get_lint_commands(rule_details))
    for pc_dep in rule_details.get(su.PC_DEPS_KEY, []):
      pc_dep = su.expand_env_vars(pc_dep)
      link_commands.append([su.PYTHON_EXPAND_LIB, pc_dep, False])
    if su.PYTHON_BIN_TYPE == rule_details[su.TYPE_KEY]:
      link_commands.append([su.PYTHON_COMPILE_ALL_CURRDIR])
    tmp_out_file = os.path.join(rule_details[su.WDIR_TARGET_KEY],
                                '.tmp.' + rule_details[su.NAME_KEY])
    link_commands.append(
        [su.PYTHON_LINK_ALL, rule_details[su.TYPE_KEY],
         main_class, tmp_out_file, rule_details[su.OUT_KEY]])
    rule_details[su.LINK_COMMANDS_KEY] = link_commands

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    coding_guidelines_check(rule_details.get(su.SRCS_KEY, []))
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY],
                      rule_details[su.WDIR_SRC_KEY],
                      rule_details[su.WDIR_TARGET_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.WDIR_SRC_KEY]])
    # File linking is more efficient than copying. However pylint does not
    # honor soft links. At the cost of performance, the only option here is to
    # actually copy the files to the build directory.
    command_list.extend(su.cp_commands_list(rule_details, su.SRCS_KEY,
                                            use_links=False))
    command_list.append([su.PYTHON_CREATE_INITIALIZERS])
    command_list.extend(rule_details[su.LINK_COMMANDS_KEY])
    return command_list


class PyLibrary(PyCommon):
  """Handler class for Python lib build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup of the rule."""
    cls._internal_setup(rule_details, details_map, False)


class PyBinary(PyCommon):
  """Handler class for Python binary build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup of the rule."""
    cls._internal_setup(rule_details, details_map, False)


class PyPyTest(PyCommon):
  """Handler class for Python test build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup of the rule."""
    cls._internal_setup(rule_details, details_map, True)
