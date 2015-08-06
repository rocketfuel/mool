"""
PyTest script to run all end-2-end tests for mool extensions.
"""
import logging
import os
import shutil
import subprocess

import file_utils as fu

BU_SCRIPT = os.path.join(os.environ['BU_SCRIPT_DIR'], 'bu')
BUILD_ROOT = os.environ['BUILD_ROOT']
TEST_DATA_DIR = os.environ['MOOL_TEST_DATA_DIR']
ECLIPSE_WORKSPACE_DIR = os.environ['ECLIPSE_WORKSPACE_DIR']
NORMALIZE_VARIABLES = ['BUILD_ROOT', 'BUILD_OUT_DIR', 'BUILD_WORK_DIR',
                       'JAVA_PROTOBUF_JAR', 'JAR_SEARCH_PATH']

UPDATE_TEST_DATA = False


def _run_cmd(cmd, stdout=subprocess.PIPE, stderr=False):
    """Runs given command and returns subprocess.Popen object."""
    stderr_dest = subprocess.STDOUT if stderr else None
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr_dest)
    proc.wait()
    return proc


def _file_grep(file_obj, pattern):
    """Checks if given file read object has pattern string.
    Note: It reads whole file as the pattern can be multiline."""
    file_text = ''.join(file_obj.readlines())
    if file_text.find(pattern) >= 0:
        return True
    return False


def _normalize(data):
    """Patches environment specific strings with mool variables."""
    for variable in NORMALIZE_VARIABLES:
        value = os.environ[variable]
        data = data.replace(value, '${%s}' % variable)
    return data


def _compare_files(expected, generated, sort=False):
    """Compares file contents of generated file with expected file."""
    def _sort_lines(data):
        """Sort all lines of data using newline as delimiter."""
        return '\n'.join(sorted(data.split('\n')))

    expected_data = fu.read_file(expected)
    generated_data = _normalize(fu.read_file(generated))
    if sort:
        expected_data = _sort_lines(expected_data)
        generated_data = _sort_lines(_normalize(fu.read_file(generated)))

    matches = _sort_lines(expected_data) == _sort_lines(generated_data)
    if not matches and UPDATE_TEST_DATA:
        fu.write_file(expected, generated_data)
    if not matches and not UPDATE_TEST_DATA:
        print 'Files {} and {} differ!'.format(expected, generated)
        print '{}\nExpected output: {}'.format('~' * 80, expected_data)
        print '{}\nGenerated output: {}'.format('~' * 80, generated_data)
    return matches


class TestDepTree():
    """Test class for dep_tree extension."""
    CMD = [BU_SCRIPT, 'dep_tree']
    RULE_NAME_ERROR = 'cannot use [ALL, LIGHTRULES] keys!'
    TEST_RULE = ('mool.jroot.src.main.java.some.work.'
                 'DriverFromDriverLibWithMissingDeps')
    TEST_RULE_EXPECTED_OUT_FILE = os.path.join(TEST_DATA_DIR, 'dep_tree.txt')

    def _get_cmd(self, rule_name):
        """Helper function to get test command."""
        cmd = list(self.CMD)
        cmd.append(rule_name)
        return cmd

    def test_bad_rules_keys(self):
        """Rules ending in ALL are not allowed."""
        for key in ['ALL', 'LIGHTRULES']:
            test_cmd = self._get_cmd('mool.x.y.z.{}'.format(key))
            proc = _run_cmd(test_cmd, stderr=True)
            print 'Return code for key %s is %d' % (key, proc.returncode)
            assert proc.returncode == 1
            assert _file_grep(proc.stdout, self.RULE_NAME_ERROR)

    def test_output(self):
        """Check if we are still getting the same good dep tree output."""
        test_cmd = self._get_cmd(self.TEST_RULE)
        proc = _run_cmd(test_cmd)
        temp_file = fu.get_temp_file(suffix='dep_tree_output')
        fu.write_file(temp_file, proc.stdout.read())
        assert proc.returncode == 0
        assert _compare_files(self.TEST_RULE_EXPECTED_OUT_FILE, temp_file)


class TestSetupEclipseProject():
    """Test class for setup_eclipse_project extension."""
    TEST_PROJECT_NAME = 'build_tools_test'
    CMD = [BU_SCRIPT, 'setup_eclipse_project', '-p', TEST_PROJECT_NAME]
    OUTPUT_DATA_DIR = os.path.join(ECLIPSE_WORKSPACE_DIR, TEST_PROJECT_NAME)
    SUCCESS_STR = 'Generated .classpath and .project files at'

    # SRC_ROOT, Inclusions, Exclusions, Classpath_file, Project_file.
    TEST1 = ('jroot/src/main/java', ['jroot/src/main/java'], [],
             'setup_eclipse_classpath_test1.txt',
             'setup_eclipse_project_test1.txt')

    TEST2 = ('jroot', ['jroot/org/personal'], ['jroot/org/personal/badjson',
             'jroot/org/personal/faillib', 'jroot/org/personal/jarMerger'],
             'setup_eclipse_classpath_test2.txt',
             'setup_eclipse_project_test2.txt')

    @classmethod
    def setup_class(cls):
        """Clean build directories and enable developer mode to download
        source jars as well."""
        _run_cmd([BU_SCRIPT, 'do_clean'])
        os.environ['DEVELOPER_MODE'] = 'true'

    @classmethod
    def setup_method(cls, method):
        """Clean any existing test generated data."""
        if os.path.exists(cls.OUTPUT_DATA_DIR):
            shutil.rmtree(cls.OUTPUT_DATA_DIR)
        if not os.path.exists(ECLIPSE_WORKSPACE_DIR):
            os.mkdir(ECLIPSE_WORKSPACE_DIR)

    def _get_cmd(self, root, inclusions, exclusions):
        """Helper function to get test command."""
        cmd = list(self.CMD)
        cmd.extend(['-r', root])
        cmd.append('-i')
        cmd.extend(inclusions)
        if any(exclusions):
            cmd.append('-e')
            cmd.extend(exclusions)
        return cmd

    def eclipse_project_setup_test(self, test_params):
        """Execute test and check expected output."""
        root, inclusions, exclusions, classfile, projectfile = test_params
        outclassfile = os.path.join(self.OUTPUT_DATA_DIR, '.classpath')
        outprojectfile = os.path.join(self.OUTPUT_DATA_DIR, '.project')
        exp_classdata = os.path.join(TEST_DATA_DIR, classfile)
        exp_projectdata = os.path.join(TEST_DATA_DIR, projectfile)
        src_link = os.path.join(self.OUTPUT_DATA_DIR, os.path.basename(root))

        proc = _run_cmd(self._get_cmd(root, inclusions, exclusions))
        assert proc.returncode == 0
        assert _compare_files(exp_classdata, outclassfile, sort=True)
        assert _compare_files(exp_projectdata, outprojectfile, sort=True)
        assert os.path.realpath(src_link) == os.path.join(BUILD_ROOT, root)

    def test_test1(self):
        """Setup project having maven directory structure."""
        self.eclipse_project_setup_test(self.TEST1)

    def test_test2(self):
        """Setup project excluding bad BLD files."""
        self.eclipse_project_setup_test(self.TEST2)

    def test_failing(self):
        """Trying to include BLD files in jroot/org/personal should fail."""
        proc = _run_cmd(self._get_cmd(self.TEST2[0], self.TEST2[1], []))
        assert proc.returncode == 1
