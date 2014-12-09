"""Hive query utilities."""
import exceptions
import os
import subprocess

import common.utils.file_utils as file_utils


def build_hiveconf_list(hive_configs):
    """Builds the -hiveconf list for calling hive."""
    arg_list = []
    if hive_configs is not None:
        for hive_config in hive_configs:
            arg_list.extend(['-hiveconf', hive_config])
    return arg_list


def call_hive_basic(query_text, hive_configs, out_file, err_file,
                    query_file=None):
    """Executes a given hive query."""
    try:
        delete_temp_file = False
        if query_file is None:
            query_file = file_utils.get_temp_file()
            delete_temp_file = True
        file_utils.write_file(query_file, query_text)
        command = ['hive']
        command.extend(build_hiveconf_list(hive_configs))
        command.extend(['-f', query_file])
        with open(err_file, 'w') as err_file_obj:
            with open(out_file, 'w') as out_file_obj:
                subprocess.check_call(command, stderr=err_file_obj,
                                      stdout=out_file_obj)
    finally:
        if delete_temp_file:
            os.remove(query_file)


def call_hive(query_text, hive_configs=None, out_file=None, err_file=None):
    """Executes a given hive query and gets the results in memory.

    Returns:
        A tuple containing (exit_code(0 for success, non-zero for failure),
                            stdout, stderr (with exception text))
    """
    tempfiles = []

    def _add_temp_file():
        """Adds a temp file to temp file cache."""
        file_name = file_utils.get_temp_file()
        tempfiles.append(file_name)
        return file_name

    try:
        out_file = out_file or _add_temp_file()
        err_file = err_file or _add_temp_file()
        call_hive_basic(query_text, hive_configs, out_file, err_file)
        return (0,
                file_utils.read_file(out_file),
                file_utils.read_file(err_file))
    except (exceptions.OSError, subprocess.CalledProcessError) as instance:
        return (1,
                file_utils.read_file(out_file),
                '\n'.join([str(instance), file_utils.read_file(err_file)]))
    finally:
        for tempfile_name in tempfiles:
            os.remove(tempfile_name)
