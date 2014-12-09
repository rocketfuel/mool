"""Tests for mool.common.utils.hive_utils."""
import subprocess
from functools import partial
import common.utils.hive_utils as hive_utils

TEST_HIVE_QUERY = 'This is a mock hive query.'
TEST_HIVE_CONFIG = ['config1', 'config2']
TEST_STDOUT_CONTENTS = 'test stdout contents'
TEST_STDERR_CONTENTS = 'test stderr contents'
TEST_HIVE_COMMAND_LINE = ['hive', '-hiveconf', 'config1', '-hiveconf',
                          'config2', '-f', 'query_file']


def test_call_hive(monkeypatch):
    """Testing the call_hive functionality."""
    def _mock_check_call(command_list, command, stderr, stdout):
        """Mock implementation of subprocess.check_call."""
        stderr.write(TEST_STDERR_CONTENTS)
        stdout.write(TEST_STDOUT_CONTENTS)
        command_list.append(command)

    command_list = []
    monkeypatch.setattr(subprocess, 'check_call',
                        partial(_mock_check_call, command_list))
    error_code, result, error_text = (
        hive_utils.call_hive(TEST_HIVE_QUERY, TEST_HIVE_CONFIG))
    assert 0 == error_code
    assert TEST_STDOUT_CONTENTS == result
    assert TEST_STDERR_CONTENTS == error_text
    command_list[0][-1] = 'query_file'
    assert [TEST_HIVE_COMMAND_LINE] == command_list
