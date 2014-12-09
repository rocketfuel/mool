#!/usr/bin/env python2.7
"""Jar testng runner utility."""
import argparse
import logging
import os
import sys
import subprocess
import zipfile
import xml.etree.ElementTree as ElementTree

TEST_METHOD_XPATH = './suite/test/class/test-method[@status=\'FAIL\']'
TRACE_COMMANDS = (os.environ.get('DEBUG_MODE', '') != '')

if __name__ == '__main__':
  SCRIPT_DIR = os.path.dirname(sys.argv[0])
  if SCRIPT_DIR != sys.path[0]:
    sys.path.insert(0, SCRIPT_DIR)

import shared_utils as su


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


def _parse_command_line():
  """Parses command line to generate arguments."""
  parser = argparse.ArgumentParser()
  parser.add_argument('--jar_path', '-j', type=str, required=True,
                      help='path to JAR (packed code) to be tested.')
  parser.add_argument('--test_classes', '-tc', type=str, nargs='+',
                      required=True, help='list of classes to test.')
  parser.add_argument('--results_dir', '-w', type=str, required=True,
                      help='directory to store testng results.')
  parser.add_argument('--groups', '-g', type=str, nargs='+', required=True,
                      help='testng groups to be tested.')
  parser.add_argument('--classpath_dir', '-cpd', type=str, default='',
                      help='path to directory to be added to classpath.')
  parser.add_argument('--java_params', '-jp', type=str, default='',
                      help='java command line args (in quotes).')
  parser.add_argument('--extract_jars', '-x', type=str, nargs='*',
                      help=('list of jars to be extracted in working '
                            'directory before test starts.'))
  return parser.parse_args()


def do_main(args):
  """Execute unit test class and print output."""
  tracer = logging.info if TRACE_COMMANDS else logging.debug
  class_path_list = [args.jar_path]
  if args.classpath_dir:
    cp_dir = args.classpath_dir
    class_path_list.extend(
        [os.path.join(cp_dir, j) for j in os.listdir(cp_dir)])
  subprocess.check_call(su.get_mkdir_command(args.results_dir))
  working_dir = os.path.join(args.results_dir, '.wdir')
  subprocess.check_call(su.get_mkdir_command(working_dir))
  if args.extract_jars:
    _extract_files_from_jars(working_dir, args.extract_jars)
  result_file = None
  try:
    test_command = [su.JAVA_RUNTIME]
    if args.java_params:
      test_command.extend(args.java_params.strip('\'').split(','))
    test_command.extend(
        ['-cp', ':'.join(class_path_list), su.JAVA_TESTNG_ROOT,
         '-d', args.results_dir, '-groups', ','.join(args.groups),
         '-testclass', ','.join(args.test_classes)])
    tracer('Command: %s', ' '.join(test_command))
    subprocess.check_call(test_command, cwd=working_dir)
  except subprocess.CalledProcessError:
    result_file = os.path.join(args.results_dir, 'testng-results.xml')
    return 1
  finally:
    if result_file:
      _display_details(result_file)


if __name__ == '__main__':
  sys.exit(do_main(_parse_command_line()))
