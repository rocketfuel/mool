"""File access utilities."""
import os
import tempfile


def get_temp_dir(suffix='', prefix='tmp', directory=None):
    """Gets a temporary directory."""
    return tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=directory)


def get_temp_file(suffix='', prefix='tmp', directory=None):
    """Gets a temporary file.

    This file path is good enough for most practical purposes. However, the
    documentation does not mention when the filename can be re-used by the
    system. Use this with sufficient amounts of fault tolerance.
    """
    handle, file_path = tempfile.mkstemp(suffix=suffix, prefix=prefix,
                                         dir=directory)
    os.close(handle)
    return file_path


def read_file(file_path, use_binary=False):
    """Reads contents of file from file path."""
    read_type = 'rb' if use_binary else 'r'
    with open(file_path, read_type) as file_obj:
        return file_obj.read()


def write_file(file_path, file_text, use_binary=False):
    """Creates (if needed) and overwrites file with specified contents."""
    write_type = 'wb' if use_binary else 'w'
    with open(file_path, write_type) as file_obj:
        file_obj.write(file_text)


def make_dir(dir_path):
    """Makes directory recursively if it does not exist."""
    if os.path.exists(dir_path):
        assert os.path.isdir(dir_path)
    else:
        os.makedirs(dir_path)
