"""Unit tests for build_utils.

The test methodology for this project is based on end-to-end strategy. Once the
project starts looking more stable, we can consider adding unit tests for each
of the rule classes.
"""
import os
import pytest

THIS_SCRIPT_DIR = os.path.join(os.environ['BU_SCRIPT_DIR'], 'unit_tests')
# We need to override the environment variables before loading the shared_utils
# module.
MOCKED_ENVIRONS = ('BUILD_OUT_DIR', 'BUILD_ROOT', 'BUILD_WORK_DIR',
                   'BU_SCRIPT_DIR', 'CC_COMPILER', 'GMOCK_DIR', 'GTEST_DIR',
                   'GTEST_MAIN_LIB', 'GTEST_MOCK_LIB', 'JAR_SEARCH_PATH',
                   'JAVA_HOME', 'PEP8_BINARY', 'PROTO_COMPILER',
                   'PYTHON_PROTOBUF_DIR')
os.environ = dict([(k, 'TEST_{}'.format(k)) for k in MOCKED_ENVIRONS])
os.environ['JAVA_COMPILER'] = 'TEST_JAVA_HOME/bin/javac -Xlint'
os.environ['JAVA_TEST_DEFAULT_JARS'] = 'test_default1.jar test_default2.jar'
os.environ['JAVA_PROTOBUF_JAR'] = 'test_java_protobuf.jar'
os.environ['JAVA_DEFAULT_VERSION'] = 'bad_version'

import shutil
import subprocess

import mool.build_utils as bu
import mool.jar_merger as jm
import mool.java_common as jc
import mool.python_common as pc
import mool.release_package as rp
import mool.shared_utils as su

from functools import partial

TEST_RESOURCES = (su.BUILD_FILE_NAME, su.SUBMIT_QUEUE_FILE_NAME)
OVERWRITE_TEST_RESOURCE = False


def _get_test_resource_file(file_name):
  """Convert file name to test resource file path."""
  return os.path.join(THIS_SCRIPT_DIR, 'test_data', file_name)


def _read_test_resource(file_name):
  """Read text from test resource."""
  file_path = _get_test_resource_file(file_name)
  with open(file_path, 'r') as file_object:
    return file_object.read()


def _write_test_resource(file_name, file_text):
  """Write text to test resource in development mode."""
  print file_text
  if not OVERWRITE_TEST_RESOURCE:
    return
  file_path = _get_test_resource_file(file_name)
  with open(file_path, 'w') as file_object:
    file_object.write(file_text)


def _mock_do_merge(command_list, lib_details, jar_out_file, main_class):
  """Mock implementation of jar merger utility."""
  command_list.append(['mock_jar_merger',
                       str([lib_details, jar_out_file, main_class])])


def _mock_exists(filesystem_dict, command_list, file_path):
  """Check if a path exists."""
  assert file_path.startswith('TEST_')
  command_list.append(['mock_ls', file_path])
  if file_path.startswith('TEST_JAR_SEARCH_PATH' + os.sep):
    return True
  if file_path in ('TEST_GTEST_MAIN_LIB', 'TEST_GTEST_MOCK_LIB'):
    return True
  return file_path in filesystem_dict


def _mock_isdir(filesystem_dict, command_list, dir_path):
  """Check if a directory exists."""
  if not dir_path.startswith('TEST_BUILD_'):
    return os.path.isdir(dir_path)
  command_list.append(['mock_isdir', dir_path])
  return dir_path in filesystem_dict


def _mock_check_dirname(filesystem_dict, dir_name):
  """Check if a dirname is valid."""
  return dir_name in filesystem_dict


def _mock_makedirs(command_list, dir_path):
  """Make directory recursively."""
  command_list.append(['mock_mkdir', '-p', dir_path])


def _mock_rmtree(command_list, dir_path):
  """Remove directory recursively."""
  command_list.append(['mock_rmtree', dir_path])


def _mock_oslistdir(dir_path):
  """Change current directory."""
  return [os.path.join(dir_path, 'mock_file1'),
          os.path.join(dir_path, 'mock_file2')]


def _mock_chdir(command_list, dir_path):
  """Change current directory."""
  command_list.append(['mock_cd', dir_path])


def _mock_download_cached_item(command_list, url, file_path):
  """Download item from URL."""
  command_list.append(['mock_download_cached_item', url, file_path])


def _mock_check_call(command_list, command):
  """Mock command line command."""
  command_list.append(command)


def _mock_read_file(filesystem_dict, command_list, file_path):
  """Mock file system reads."""
  assert file_path in filesystem_dict
  command_list.append(['mock_cat', file_path])
  return filesystem_dict[file_path]


def _mock_write_file(command_list, file_path, file_text):
  """Mock file system writes."""
  file_text = file_text.replace('\n', '\\n')
  command_list.append(['mock_write', file_path, '"{}"'.format(file_text)])


def _mock_python_compile_all(command_list, params):
  """Mock python compiler step."""
  command_list.append(['mock_python_compile_all', str(params)])


def _mock_python_expand_lib(command_list, params):
  """Mock python expand linked library in place."""
  command_list.append(['mock_python_expand_lib', str(params)])


def _mock_py_create_initializers(command_list, params):
  """Mock python create_initializers call."""
  command_list.append(['create_initializers', str(params)])


def _mock_coding_guidelines_check(command_list, params):
  """Mock additional python coding guidelines check."""
  command_list.append(['mock_coding_guidelines_check', str(params)])


def _mock_python_perform_linking(command_list, command_parts):
  """Mock python linking step."""
  command_list.append(['mock_python_perform_linking', str(command_parts)])


def _mock_zip_all_currdir(command_list, command_parts):
  """Mock python linking step."""
  command_list.append(['mock_zip_all_currdir', str(command_parts)])


def _mock_compare_java_version(command_list, rule_version, dep_version):
  """Mock java version comparison check."""
  command_list.append(['mock_java_version_comparison', rule_version,
                       dep_version])
  return True


def _patch_os(monkeypatch, filesystem_dict, command_list):
  """Apply monkeypatch on system libraries."""
  monkeypatch.setattr(su, 'path_exists',
                      partial(_mock_exists, filesystem_dict, command_list))
  monkeypatch.setattr(os.path, 'isdir',
                      partial(_mock_isdir, filesystem_dict, command_list))
  monkeypatch.setattr(os, 'makedirs', partial(_mock_makedirs, command_list))
  monkeypatch.setattr(os, 'chdir', partial(_mock_chdir, command_list))
  monkeypatch.setattr(os, 'listdir', _mock_oslistdir)
  monkeypatch.setattr(shutil, 'rmtree', partial(_mock_rmtree, command_list))
  monkeypatch.setattr(subprocess, 'check_call',
                      partial(_mock_check_call, command_list))
  monkeypatch.setattr(bu, 'SHOW_ERRORS', False)

  monkeypatch.setattr(jc, 'compare_java_versions',
                      partial(_mock_compare_java_version, command_list))
  monkeypatch.setattr(jm, 'do_merge', partial(_mock_do_merge, command_list))
  monkeypatch.setattr(su, 'DUMMY_CC', 'DUMMY_CC_FILE')
  monkeypatch.setattr(su, 'check_dirname',
                      partial(_mock_check_dirname, filesystem_dict))
  monkeypatch.setattr(su, 'read_file',
                      partial(_mock_read_file, filesystem_dict, command_list))
  monkeypatch.setattr(su, 'write_file',
                      partial(_mock_write_file, command_list))
  monkeypatch.setattr(su, 'lock_working_dir', lambda: None)
  monkeypatch.setattr(su, 'needs_build', lambda _, __: True)
  monkeypatch.setattr(su, 'release_working_dir', lambda _: None)
  monkeypatch.setattr(su, 'save_file_list_cache', lambda _, __: None)
  monkeypatch.setattr(pc, 'compile_all',
                      partial(_mock_python_compile_all, command_list))
  monkeypatch.setattr(pc, 'expand_lib',
                      partial(_mock_python_expand_lib, command_list))
  monkeypatch.setattr(pc, 'perform_linking',
                      partial(_mock_python_perform_linking, command_list))
  monkeypatch.setattr(pc, 'create_initializers',
                      partial(_mock_py_create_initializers, command_list))
  monkeypatch.setattr(pc, 'coding_guidelines_check',
                      partial(_mock_coding_guidelines_check, command_list))
  monkeypatch.setattr(su, 'download_cached_item',
                      partial(_mock_download_cached_item, command_list))
  monkeypatch.setattr(rp, 'zip_all_currdir',
                      partial(_mock_zip_all_currdir, command_list))


def _get_commands(monkeypatch, filesystem_dict, rules_list):
  """Test command sequence."""
  command_list = []
  _patch_os(monkeypatch, filesystem_dict, command_list)
  monkeypatch.setattr(su, 'TEST_MODE_EXECUTION', True)
  dependency_dict = {}
  result = bu.apply_rules(rules_list, dependency_dict)
  assert 0 == result
  actual_dep_list = []
  for rule_symbol, rule_deps in sorted(dependency_dict.iteritems()):
    actual_dep_list.append(rule_symbol)
    rule_deps.sort()
    for dep in rule_deps:
      actual_dep_list.append('-->{}'.format(dep))
  return ('\n'.join([' '.join(c) for c in command_list]), actual_dep_list)


def _get_filesystem_dict():
  """Get in-memory filesystem dictionary."""
  file_list = [
      f.strip() for f in _read_test_resource('file_list.txt').split('\n')
      if f.strip()]
  filesystem_dict = dict([(f, '') for f in file_list])
  for file_name in file_list:
    if os.path.basename(file_name) in TEST_RESOURCES:
      filesystem_dict[file_name] = _read_test_resource(
          file_name.replace(os.sep, '_') + '.txt')
  return filesystem_dict


def test_null_sequence(monkeypatch):
  """Test command sequence."""
  actual_commands, dependency_list = _get_commands(monkeypatch, {}, [])
  assert '' == actual_commands
  assert not dependency_list


def test_clean(monkeypatch):
  """Test clean command sequence."""
  expected_commands = _read_test_resource('clean_command_steps.txt').strip()
  assert (expected_commands, []) == _get_commands(monkeypatch, {},
                                                  [bu.CLEAN_COMMAND])


def test_null_commands(monkeypatch):
  """Test clean command sequence."""
  with pytest.raises(bu.Error):
    _get_commands(monkeypatch, {}, [bu.BUILD_COMMAND])
  with pytest.raises(bu.Error):
    _get_commands(monkeypatch, {}, [bu.TEST_COMMAND])


def _test_command_utility(monkeypatch, op_command, rules_text,
                          build_deps_file, build_commands_file):
  """Utility function for end to end test of specifed build rules."""
  def _get_debug_dep_list(actual_dep_list):
    """Print actual commands. Used for updating test data."""
    lines = '\n'.join(actual_dep_list)
    lines = lines.replace('-->', '    -->')
    lines = lines.replace(su.RULE_ROOT_NAME, '\n' + su.RULE_ROOT_NAME)
    return '{}\n'.format(lines.strip('\n'))

  filesystem_dict = _get_filesystem_dict()
  rules_list = [op_command]
  rules_list.extend([r for r in rules_text.split() if r])
  actual_commands, actual_dep_list = _get_commands(
      monkeypatch, filesystem_dict, rules_list)
  expected_build_deps = _read_test_resource(build_deps_file)
  expected_dep_list = [
      l.strip() for l in expected_build_deps.split('\n') if l.strip()]
  if expected_dep_list != actual_dep_list:
    _write_test_resource(build_deps_file,
                         _get_debug_dep_list(actual_dep_list))
  assert expected_dep_list == actual_dep_list
  actual_commands = actual_commands.strip()
  expected_commands = _read_test_resource(build_commands_file).strip()
  if expected_commands != actual_commands:
    _write_test_resource(build_commands_file, '\n'.join([actual_commands, '']))
  assert expected_commands == actual_commands


def test_simple_cc_command(monkeypatch):
  """Test simple build command for C++ rules."""
  _test_command_utility(monkeypatch, bu.BUILD_COMMAND,
                        'mool.cc.common.echo_utils_test',
                        'simple_cc_command_build_deps.txt',
                        'simple_cc_command_steps.txt')


def test_complex_cc_command(monkeypatch):
  """Test complex command for C++ rules."""
  rules_text = """
    mool.cc.samples.factorial_test mool.cc.samples.factorial_main
    mool.cc.common.echo_utils_test mool.cc.samples.person_proto_main"""
  _test_command_utility(monkeypatch, bu.TEST_COMMAND, rules_text,
                        'complex_cc_command_build_deps.txt',
                        'complex_cc_command_steps.txt')


def test_complex_java_command(monkeypatch):
  """Test complex command for Java rules."""
  rules_text = """
    mool.src.main.java.some.other.work.HelloWorld
    mool.src.test.java.some.other.work.HelloWorldTest
    mool.src.main.java.some.work.Driver
    mool.src.main.java.some.work.DriverFromMavenSpec
    mool.src.main.java.some.work.DriverLibWithExcludedCompileDeps
    mool.src.main.java.some.work.DriverLibWithExcludedDeps
    mool.src.main.java.some.work.DriverLibWithIncludedCompileDeps
    mool.src.main.java.some.work.DriverLibWithIncludedDeps
    mool.src.main.java.some.work.DriverFromDriverLibWithExcludedCompileDeps
    mool.src.main.java.some.work.DriverFromDriverLibWithExcludedDeps
    mool.src.main.java.some.work.DriverFromDriverLibWithIncludedCompileDeps
    mool.src.main.java.some.work.DriverFromDriverLibWithIncludedDeps
    mool.src.test.java.some.work.DriverTest
    mool.src.main.java.some.work.BinWithNoDependencies
    mool.src.main.java.some.work.ProtoSampleMain
    mool.src.test.java.some.work.DriverTestIntegration"""
  _test_command_utility(monkeypatch, bu.TEST_COMMAND, rules_text,
                        'complex_java_command_build_deps.txt',
                        'complex_java_command_steps.txt')


def test_release_package_command(monkeypatch):
  """Test release package rule."""
  rules_text = 'mool.src.main.java.some.work.complete_package'
  _test_command_utility(monkeypatch, bu.BUILD_COMMAND, rules_text,
                        'release_package_command_build_deps.txt',
                        'release_package_command_steps.txt')


def test_complex_python_command(monkeypatch):
  """Test complex command for Python rules."""
  rules_text = """
    mool.py.first_service.first_module.ALL
    mool.py.second_service.another_module.ALL"""
  _test_command_utility(monkeypatch, bu.TEST_COMMAND, rules_text,
                        'complex_python_command_build_deps.txt',
                        'complex_python_command_steps.txt')


def test_build_all(monkeypatch):
  """Test list of effective build rules with ALL command."""
  filesystem_dict = _get_filesystem_dict()
  rules_text = ('mool.cc.samples.ALL mool.cc.common.ALL '
                'mool.src.main.java.some.work.ALL '
                'mool.py.first_service.first_module.ALL '
                'mool.py.second_service.another_module.ALL')
  rules_list = [bu.BUILD_COMMAND]
  rules_list.extend([r for r in rules_text.split() if r])
  _, dependency_list = _get_commands(monkeypatch, filesystem_dict, rules_list)
  expected_list = _read_test_resource('all_rules_list.txt').strip().split()
  actual_list = [d for d in dependency_list if su.RULE_ROOT_NAME in d]
  assert sorted(expected_list) == sorted(actual_list)


def test_build_lightrules(monkeypatch):
  """Test list of effective build rules with LIGHTRULES command."""
  filesystem_dict = _get_filesystem_dict()
  rules_text = ('mool.cc.samples.LIGHTRULES mool.cc.common.LIGHTRULES '
                'mool.src.main.java.some.work.LIGHTRULES '
                'mool.py.first_service.first_module.LIGHTRULES '
                'mool.py.second_service.another_module.LIGHTRULES')
  rules_list = [bu.BUILD_COMMAND]
  rules_list.extend([r for r in rules_text.split() if r])
  _, dependency_list = _get_commands(monkeypatch, filesystem_dict, rules_list)
  expected_list = _read_test_resource('light_rules_list.txt').strip().split()
  actual_list = [d for d in dependency_list if su.RULE_ROOT_NAME in d]
  assert sorted(expected_list) == sorted(actual_list)


def test_submit_queue_list(monkeypatch):
  """Test submit queue list."""
  def _validate_test_list(expected_tests, changed_files):
    """Compare actual and expected test lists."""
    changed_files = [os.path.join(su.BUILD_ROOT, f) for f in changed_files]
    actual_tests = su.get_affected_rules(changed_files)
    assert expected_tests == actual_tests

  _patch_os(monkeypatch, _get_filesystem_dict(), [])
  _validate_test_list([], [])
  _validate_test_list(
      ['mool.cc.samples.factorial_test',
       'mool.src.main.java.some.other.work.LIGHTRULES',
       'mool.src.test.java.some.other.work.HelloWorldTest'],
      ['src/main/java/some/other/work/any_file'])
  _validate_test_list(
      ['mool.cc.samples.LIGHTRULES', 'mool.cc.samples.factorial_test',
       'mool.cc.samples.use_interface_test',
       'mool.src.main.java.some.other.work.LIGHTRULES',
       'mool.src.test.java.some.other.work.HelloWorldTest'],
      ['src/main/java/some/other/work/any_file',
       'cc/samples/dir1/dir2/dir3/some_file'])
  _validate_test_list(
      ['mool.cc.samples.LIGHTRULES', 'mool.cc.samples.factorial_test',
       'mool.cc.samples.use_interface_test',
       'mool.src.main.java.some.other.work.LIGHTRULES',
       'mool.src.main.java.some.work.LIGHTRULES',
       'mool.src.test.java.some.other.work.HelloWorldTest',
       'mool.src.test.java.some.other.work.LIGHTRULES',
       'mool.src.test.java.some.work.DriverTest'],
      ['src/main/java/some/other/work/any_file',
       'src/main/java/some/work/another_file',
       'src/test/java/some/other/work/some_test_file',
       'cc/samples/dir1/dir2/dir3/some_file'])
