"""
This script checks the python specific mool tests.
Environment variables should be set before running this script.

Ensure exit on first failure!!
"""

import logging
import os
import subprocess
import sys
import zipfile

import file_utils as fu
import tests_config as tc

LOGGER = None
BU_SCRIPT_DIR = os.environ['BU_SCRIPT_DIR']
BU_SCRIPT = os.path.join(BU_SCRIPT_DIR, 'bu')
BUILD_ROOT = os.environ['BUILD_ROOT']
BUILD_OUT_DIR = os.environ['BUILD_OUT_DIR']
LOG_FILE_PATH = os.environ['MOOL_TESTS_LOG_FILE']
SKIP_BUILD_STRING = 'Skipping build for mool'
EMIT_BUILD_STRING = 'Emitting'


class Error(Exception):
    """Error class."""
    def __exit__(self, etype, value, traceback):
        LOGGER.error(str(self.message))


def configure_logging(console=True):
    """Setup logging. Enable console logging by default."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if console:
        console_handle = logging.StreamHandler(sys.stdout)
        console_handle.setLevel(logging.DEBUG)
        console_handle.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(console_handle)
    return logger


def validate_pattern_count(expected_count, pattern, file_path):
    """Check given ZIP has expected_count number of files matching pattern."""
    zipped_files = None
    with zipfile.ZipFile(file_path, 'r') as zip_obj:
        zipped_files = zip_obj.namelist()
    match_count = len(
        [name for name in zipped_files if name.find(pattern) >= 0])
    if not expected_count == match_count:
        LOGGER.error('Unexpected number of pattern lines: %d', match_count)
        LOGGER.error('  Expected number of pattern lines: %d', expected_count)
        raise Error('Failed validating pattern count for %s.' % file_path)


def check_file_count(expected_count, file_path):
    """Check given JAR file has expected_count number of files."""
    zipped_file_count = 0
    with zipfile.ZipFile(file_path, 'r') as zip_obj:
        zipped_file_count = len(zip_obj.namelist())
    if not zipped_file_count == expected_count:
        LOGGER.error('Unexpected file count: %d', zipped_file_count)
        LOGGER.error('  Expected file count: %d', expected_count)
        raise Error('Failed checking file count for %s.' % file_path)


def check_jar_contents(filename, jar_full_path):
    """Check if given JAR contains a file with name filename."""
    LOGGER.debug('Checking %s in %s.', filename, jar_full_path)
    with zipfile.ZipFile(jar_full_path, 'r') as zipfile_obj:
        if not filename in zipfile_obj.namelist():
            LOGGER.error('File "%s" missing in "%s".', filename, jar_full_path)
            raise Error('Failed validating JAR contents!!')


def check_submitq_test(expected_tests, changed_files):
    """Check if submit queue outputs expected tests for given changed files."""
    LOGGER.debug('Running SUBMITQ tests on: [%s].', ', '.join(changed_files))
    try:
        # In debug mode, the tests are only listed. Otherwise the tests are
        # actually executed.
        os.environ['SUBMITQ_DEBUG_MODE'] = 'true'
        input_file = fu.get_temp_file()
        output_file = fu.get_temp_file()
        input_data = [os.path.join(BUILD_ROOT, f) for f in changed_files]
        fu.write_file(input_file, '\n'.join(input_data))
        with open(output_file, 'w') as stdout_obj:
            subprocess.check_call([BU_SCRIPT, 'do_test_changes', input_file],
                                  stdout=stdout_obj)
        actual_tests = [l for l in fu.read_file(output_file).split('\n') if l]
        expected_tests.sort()
        actual_tests.sort()
        if expected_tests != actual_tests:
            LOGGER.error('Expected tests: %s', ' '.join(expected_tests))
            LOGGER.error('  Actual tests: %s', ' '.join(actual_tests))
            raise Error('SUBMITQ tests failed!!')
    finally:
        os.remove(input_file)
        os.remove(output_file)


def validate_binary_output(binary_path, grep_items):
    """Check thae given binary has all the list of patterns."""
    LOGGER.debug('Checking output of %s binary.', binary_path)
    try:
        output_file = fu.get_temp_file()
        with open(output_file, 'w') as stdout_obj:
            subprocess.check_call(binary_path, stdout=stdout_obj)
        stdout_lines = fu.read_file(output_file).split('\n')
        for grep_item in grep_items:
            matched_lines = [line for line in stdout_lines if grep_item in line]
            if not matched_lines:
                LOGGER.error('Expected pattern: %s', grep_item)
                LOGGER.error('   Actual output: %s', '\n'.join(stdout_lines))
                msg = 'Binary output validation failed for %s!!' % binary_path
                raise Error(msg)
    finally:
        os.remove(output_file)


def validate_build_fails(build_rule, grep_items):
    """Verify that the given build_rule fails and errors have grep patterns."""
    try:
        output_file = fu.get_temp_file()
        build_cmd = [BU_SCRIPT, 'do_build', build_rule]
        subprocess.check_output(build_cmd, stderr=subprocess.STDOUT)
        raise Error('Build rule "%s" must fail but it passed!', build_rule)
    except subprocess.CalledProcessError as exp:
        output = exp.output
        for grep_item in grep_items:
            if output.find(grep_item) < 0:
                LOGGER.error('Pattern: "%s" not found in output!', grep_item)
                LOGGER.error('Full output: %s', output)
                raise Error('Didn\'t find expected pattern in output!')
        LOGGER.info('Build rule "%s" failed as expected.', build_rule)
    finally:
        os.remove(output_file)


def check_no_pyc(dir_to_check):
    """Recursively check for existence of .pyc files."""
    LOGGER.debug('Checking .pyc files in %s.', dir_to_check)
    for root, ___, files in os.walk(dir_to_check):
        if '__pycache__' in root:
            raise Error('__pycache__ directory found in %s!!' % root)
        for file_path in files:
            full_file_path = os.path.join(root, file_path)
            if full_file_path.endswith('.pyc'):
                raise Error('Compiled binary %s found.' % full_file_path)


def execute_and_log(cmd, grep_str=None):
    """
    Executes the cmd using subprocess Popen and logs the output to logging
    object. Returns match count corresponding to grep_str if it is not None.
    """
    pattern_count = 0
    LOGGER.info('Executing "%s"', ' '.join(cmd))
    with open(os.devnull, 'w') as devnull:
        with open(LOG_FILE_PATH, 'w') as logfile:
            subprocess.check_call(cmd, stdout=devnull, stderr=logfile)
    if grep_str:
        with open(LOG_FILE_PATH, 'r') as logfile:
            lines = logfile.read().split('\n')
            pattern_count = len([line for line in lines
                                 if line.find(grep_str) >= 0])
    return pattern_count


def test_touch_bld_file():
    """Test that a changed BLD file triggers build for all the rules."""
    build_rule, build_file, rebuilds = tc.BLD_TOUCH_TEST
    build_cmd = [BU_SCRIPT, 'do_build', build_rule]
    execute_and_log(build_cmd)
    count = execute_and_log(build_cmd, grep_str=EMIT_BUILD_STRING)
    if count != 0:
        LOGGER.error('Unexpected number of builds emitted: %s', count)
        LOGGER.error('  Expected number of builds emitted: 0')
        raise Error('Skip all builds test failed!!')
    build_file = os.path.join(BUILD_ROOT, build_file)
    execute_and_log(['touch', '-f', build_file])
    count = execute_and_log(build_cmd, grep_str=EMIT_BUILD_STRING)
    if count != rebuilds:
        LOGGER.error('Unexpected number of builds emitted: %s', count)
        LOGGER.error('  Expected number of builds emitted: %s', rebuilds)
        raise Error('Touching BLD file didn\'t trigger expected builds!!')


def misc_tests():
    """Run all miscellaneous tests."""
    test_touch_bld_file()
    for build_rule, grep_items in tc.BUILD_FAIL_TESTS:
        validate_build_fails(build_rule, grep_items)


def adhoc_tests():
    """Build and test file collection, binary output and SUBMITQ tests."""
    for res_file, jars_to_check in tc.FILE_COLLECTION_TESTS:
        for jar in jars_to_check:
            check_jar_contents(res_file, os.path.join(BUILD_OUT_DIR, jar))

    for expected_tests, changed_files in tc.SUBMITQ_TESTS:
        check_submitq_test(expected_tests, changed_files)

    for binary, patterns in tc.VALIDATE_BINARY_OUTPUT:
        validate_binary_output(os.path.join(BUILD_OUT_DIR, binary), patterns)

    check_no_pyc(os.path.join(BUILD_ROOT, 'pyroot'))


def regression_tests():
    """Build and test regression tests."""
    build_cmd = [BU_SCRIPT, 'do_build']
    build_cmd.extend(tc.REG_BUILD_RULES)
    execute_and_log(build_cmd)

    for test in tc.REG_PATTERN_TESTS:
        count, pattern, file_path = test
        full_path = os.path.join(BUILD_OUT_DIR, file_path)
        validate_pattern_count(count, pattern, full_path)
    LOGGER.info('Regression tests passed!!')


def build_test_all_rules():
    """Build and test all rules."""
    build_cmd = [BU_SCRIPT, 'do_build']
    build_cmd.extend(tc.BUILD_RULES)
    execute_and_log(build_cmd)

    for count, file_path in tc.FILE_COUNT_TESTS:
        full_path = os.path.join(BUILD_OUT_DIR, file_path)
        check_file_count(count, full_path)

    for count, pattern, file_path in tc.PATTERN_TESTS:
        full_path = os.path.join(BUILD_OUT_DIR, file_path)
        validate_pattern_count(count, pattern, full_path)

    # Execute all tests from BUILD_TESTS.
    test_cmd = [BU_SCRIPT, 'do_test']
    test_cmd.extend(tc.BUILD_TESTS)
    test_cmd.extend(tc.BUILD_RULES)
    execute_and_log(test_cmd)

    test_cmd = [BU_SCRIPT, 'do_build']
    test_cmd.extend(tc.BUILD_RULES)
    pattern_count = execute_and_log(test_cmd, grep_str=SKIP_BUILD_STRING)
    if pattern_count is not tc.SKIPPED_BUILD_COUNT:
        LOGGER.error(('Unexpected number of skipped builds: %d\n'
                      'Expected number: %d'), pattern_count,
                     tc.SKIPPED_BUILD_COUNT)
        raise Error('Skipped builds check failed.')

    # Test all executables.
    java_exec = os.path.join(os.environ['JAVA_HOME'], 'bin', 'java')
    for exec_params in tc.EXECUTABLES_TO_RUN:
        executable = exec_params[0] if len(exec_params) == 2 else exec_params
        options = exec_params[1] if len(exec_params) == 2 else []
        command = []
        if executable.endswith('.jar'):
            command.append(java_exec)
            command.extend(options)
            command.extend(['-jar', '-ea'])
        command.append(os.path.join(BUILD_OUT_DIR, executable))
        execute_and_log(command)


def do_main():
    """Builds and executes all tests."""
    # Start from a clean state.
    execute_and_log([BU_SCRIPT, 'do_clean'])

    regression_tests()
    build_test_all_rules()
    adhoc_tests()
    misc_tests()

    LOGGER.info('---------------------------------------------')
    LOGGER.info('All java and python code root tests passed!!!')


if __name__ == "__main__":
    LOGGER = configure_logging()
    LOGGER.info('Check %s for errors from last build.', LOG_FILE_PATH)
    do_main()
