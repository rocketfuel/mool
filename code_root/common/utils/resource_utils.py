"""Utilities for handling file based resources."""
import os
import sys
import zipfile

import common.utils.file_utils as file_utils

MODULE_PATH = os.path.realpath(sys.argv[0])
TEST_MODULE = 'py.test'


def read_resource(resource_path):
    """Read a resource file from python mool binary."""
    if MODULE_PATH.endswith(TEST_MODULE):
        # For py.test implementation, the current directory contains the
        # unzipped files.
        return file_utils.read_file(resource_path)
    with zipfile.ZipFile(MODULE_PATH, 'r') as zip_obj:
        with zip_obj.open(resource_path) as zipfile_obj:
            return zipfile_obj.read()
