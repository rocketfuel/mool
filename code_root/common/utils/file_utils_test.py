"""Tests for mool.common.utils.file_utils.

These tests do touch the disk. Hopefully, these libraries would not change too
often.
"""
import os
import shutil

import common.utils.file_utils as file_utils
# TODO: Add more tests involving un-tested parameters of file_utils functions.

TEST_DIR = '/tmp'
TEST_DIR_PREFIX = os.path.join(TEST_DIR, '')
TEST_CONTENTS = 'Mary had a little lamb.'


def test_get_temp_dir():
    """Testing get_temp_dir().

    Make sure that the directory gets created in the specified directory and
    it is writeable by current user.
    """
    temp_dir = file_utils.get_temp_dir(directory=TEST_DIR)
    assert temp_dir.startswith(TEST_DIR_PREFIX)
    shutil.rmtree(temp_dir)


def test_get_temp_file():
    """Testing get_temp_file().

    Make sure that the file gets created in the specified directory and
    it is writeable by current user.
    """
    temp_file = file_utils.get_temp_file(directory=TEST_DIR)
    assert temp_file.startswith(TEST_DIR_PREFIX)
    os.remove(temp_file)


def test_read_write_file():
    """Testing file read and file write api's."""
    temp_file = file_utils.get_temp_file(directory=TEST_DIR)
    assert '' == file_utils.read_file(temp_file)
    file_utils.write_file(temp_file, '')
    assert '' == file_utils.read_file(temp_file)
    file_utils.write_file(temp_file, TEST_CONTENTS)
    assert TEST_CONTENTS == file_utils.read_file(temp_file)
    os.remove(temp_file)


def test_make_dir():
    """Test recursive make dir function."""
    temp_dir = file_utils.get_temp_dir(directory=TEST_DIR)
    child1_dir = os.path.join(temp_dir, 'child1')
    child2_dir = os.path.join(child1_dir, 'child2')
    assert not os.path.exists(child1_dir)
    assert not os.path.exists(child2_dir)
    file_utils.make_dir(child2_dir)
    assert os.path.exists(child1_dir)
    assert os.path.exists(child2_dir)
    shutil.rmtree(temp_dir)
