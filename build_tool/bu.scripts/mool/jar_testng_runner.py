"""Jar testng runner utility."""
import logging
import os
import subprocess
import zipfile
import xml.etree.ElementTree as ElementTree

import mool.jar_merger as jm
import mool.shared_utils as su

TEST_METHOD_XPATH = './suite/test/class/test-method[@status=\'FAIL\']'

CLASHING_DEPS_MSG = (
    'WARN: Clashes have been found in your test dependencies. Your tests may '
    'be passing/failing due to wrong runtime dependencies you are not aware '
    'of. FIX this to have sound sleep while your code is in production!!')


def _display_details(result_file):
  """Display details of test result file, if any."""
  def _line_ok(stack_trace_line):
    """Filter out unnecessary lines from test failure call stack."""
    if 'at org.testng.' in stack_trace_line:
      return False
    if 'at sun.reflect.' in stack_trace_line:
      return False
    if 'at java.lang.reflect.' in stack_trace_line:
      return False
    return True

  if not os.path.exists(result_file):
    return
  print 'Detailed results at: {}\n'.format(su.log_normalize(result_file))
  node_root = ElementTree.parse(result_file).getroot()
  for test_method in node_root.findall(TEST_METHOD_XPATH):
    print '---------------------------------------------'
    print test_method.attrib['signature']
    stack_text = test_method.findall('./exception/full-stacktrace')[0].text
    stack_text_lines = [l for l in stack_text.strip().split('\n')
                        if _line_ok(l)]
    print '\n'.join(stack_text_lines)
    print


def _extract_files_from_jars(work_dir, jar_list):
  """Extract given list of jars into working directory."""
  for jar_file in jar_list:
    with zipfile.ZipFile(jar_file) as jar_obj:
      jar_obj.extractall(path=work_dir)


def do_main(args):
  """Execute unit test class and print output."""
  jar_path, test_classes, results_dir, test_groups, classpath_dir = args[0:5]
  java_params, extract_jars = args[5:7]

  class_path_list = [jar_path]
  class_path_list.extend(
      [os.path.join(classpath_dir, j) for j in os.listdir(classpath_dir)])
  subprocess.check_call(su.get_mkdir_command(results_dir))
  working_dir = os.path.join(results_dir, '.wdir')
  subprocess.check_call(su.get_mkdir_command(working_dir))

  _extract_files_from_jars(working_dir, extract_jars)
  result_file = None
  clashes_found = jm.check_jar_collisions(class_path_list)
  try:
    test_command = [su.JAVA_RUNTIME]
    test_command.extend(java_params)
    test_command.extend(
        ['-ea', '-cp', ':'.join(class_path_list), su.JAVA_TESTNG_ROOT,
         '-d', results_dir, '-groups', ','.join(test_groups),
         '-testclass', ','.join(test_classes)])
    logging.debug('Command: %s', ' '.join(test_command))
    subprocess.check_call(test_command, cwd=working_dir)
  except subprocess.CalledProcessError:
    result_file = os.path.join(results_dir, 'testng-results.xml')
    _display_details(result_file)
    raise
  finally:
    if clashes_found:
      print CLASHING_DEPS_MSG
