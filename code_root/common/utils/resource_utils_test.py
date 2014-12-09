"""Tests for mool.common.utils.resource_utils."""
import os
import subprocess

import common.utils.resource_utils as resource_utils
import common.utils.test_modules.validation_outer as vo


def test_read_resource_from_lib():
    """Test reading resource from a linked library."""
    vo.validate_outer()


def test_read_resource_from_bin():
    """Test reading resource from a binary."""
    validation_bin = os.path.join(
        os.environ['BUILD_OUT_DIR'], 'common', 'utils', 'test_modules',
        'validation_bin')
    subprocess.check_call(validation_bin)


def test_read_resource_linked_directly():
    """Test reading resource linked directly to unit test."""
    assert '789' == resource_utils.read_resource('v_resources/file3.txt')
