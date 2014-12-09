"""Implement the rules of release package build rule."""
import logging
import os
import subprocess
import zipfile

import shared_utils as su


def zip_all_currdir(params):
  """Zip all contents of current directory to target file."""
  assert 1 == len(params)
  target_file = params[0]
  tmp_file = target_file + '.tmp'
  with zipfile.ZipFile(tmp_file, 'w') as zip_obj:
    for root, _, files in os.walk('.'):
      for file_path in files:
        zip_obj.write(os.path.join(root, file_path))
  subprocess.check_call(['mv', tmp_file, target_file])


class ReleasePackage(object):
  """Pre-release test and packaging module."""
  @classmethod
  def _setup_deps(cls, rule_details, details_map):
    """Setup all dependencies."""
    all_dep_paths = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      all_dep_paths.append(details_map[rule_symbol][su.OUT_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY] = sorted(list(set(all_dep_paths)))

  @classmethod
  def _setup_tests(cls, rule_details, details_map):
    """Setup all tests."""
    test_commands = []
    for rule_symbol in rule_details.get(su.PACKAGE_TESTS_KEY, []):
      test_commands.append(['echo', 'Testing', rule_symbol])
      test_commands.extend(details_map[rule_symbol][su.TEST_COMMANDS_KEY])
    rule_details[su.RELEASE_TEST_COMMANDS_KEY] = test_commands

  @classmethod
  def _setup_linking(cls, rule_details, details_map):
    """Setup linking final output."""
    link_commands = [[su.CHANGE_CURR_DIR, rule_details[su.WDIR_KEY]]]
    possible_prefixes = su.prefix_transform([su.BUILD_OUT_DIR])
    for rule_symbol in rule_details.get(su.PACKAGE_MODULES_KEY, []):
      src_file = details_map[rule_symbol][su.OUT_KEY]
      dst_file = su.get_relative_path(possible_prefixes, src_file)
      link_commands.append(su.get_mkdir_command(os.path.dirname(dst_file)))
      link_commands.append(su.get_copy_command(src_file, dst_file, True))
    link_commands.append(
        [su.PERFORM_ZIP_ALL_CURRDIR, rule_details[su.OUT_KEY]])
    rule_details[su.LINK_COMMANDS_KEY] = link_commands

  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup of the rule."""
    out_file = rule_details[su.NAME_KEY] + '.zip'
    su.init_rule_common(rule_details, out_file, [])
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    cls._setup_deps(rule_details, details_map)
    cls._setup_tests(rule_details, details_map)
    cls._setup_linking(rule_details, details_map)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.extend(rule_details[su.RELEASE_TEST_COMMANDS_KEY])
    command_list.extend(rule_details[su.LINK_COMMANDS_KEY])
    return command_list
