"""Jar merger utility."""
import hashlib
import logging
import os
import shutil
import subprocess

import shared_utils as su


# We delete a few temporary files in this module. Let's make
# sure that the files are at least in the working directories
# of the current build step. It makes sense to ignore symbolic
# names in this check.
BUILD_OUT_DIR = os.path.realpath(su.BUILD_OUT_DIR)
BUILD_WORK_DIR = os.path.realpath(su.BUILD_WORK_DIR)

BLOCK_SIZE = (1L << 20)
MAX_CLEANUP_DEPTH = 20
MAX_DEBUG_LEN = 4


class Error(Exception):
  """The exception class for this module."""


def _hash_file_text(file_path):
  """Get hash contents of a file from its path."""
  hash_object = hashlib.md5()
  with open(file_path, 'r') as file_object:
    while True:
      file_text = file_object.read(BLOCK_SIZE)
      if not file_text:
        break
      hash_object.update(file_text)
  return hash_object.hexdigest()


def _file_signature(file_path):
  """Gets the textual signature of a file version on disk."""
  size_bytes = os.stat(file_path).st_size
  return (file_path, str(size_bytes), _hash_file_text(file_path))


def _get_all_files_in_dir(dir_path):
  """Get all files in directory path."""
  result = []
  for root, _, files in os.walk(dir_path):
    if not files:
      continue
    temp_list = [os.path.join(root, f) for f in files]
    temp_list = [_file_signature(f) for f in temp_list]
    result.extend(temp_list)
  return result


def _get_all_empty_dirs(dir_path):
  """Get all empty directories under dir_path."""
  return [root for (root, dirs, files) in os.walk(dir_path)
          if (not dirs and not files and root != dir_path)]


def _get_temp_dir(jar_out_file, prefix):
  """Get the temporary directory to build out the jar file."""
  basename = os.path.basename(jar_out_file)
  dirname = os.path.dirname(jar_out_file)
  temp_dir = os.path.join(dirname, '.{}.{}'.format(prefix, basename))
  os.makedirs(temp_dir)
  return temp_dir


def _check_and_remove(file_path):
  """Check if file exists and remove it."""
  file_path = os.path.realpath(file_path)
  ok_to_delete = (
      file_path.startswith(BUILD_WORK_DIR) or
      file_path.startswith(BUILD_OUT_DIR))
  if not ok_to_delete:
    logging.error('%s is not safe to delete.', file_path)
  assert ok_to_delete
  if os.path.exists(file_path):
    if os.path.isdir(file_path):
      shutil.rmtree(file_path)
    else:
      os.remove(file_path)


def _do_cleanup(dir_path, inclusions, exclusions):
  """Apply inclusion, exclusion and cleanup."""
  for excluded_file in exclusions:
    _check_and_remove(os.path.join(dir_path, excluded_file))
  if inclusions:
    inclusions = [os.path.join(dir_path, f) for f in inclusions]
    all_files = [f[0] for f in _get_all_files_in_dir('.')]
    files_to_delete = [f for f in all_files if f not in inclusions]
    for file_path in files_to_delete:
      _check_and_remove(file_path)
  # A somewhat inefficient mechanism of recursively cleaning up empty
  # directories under dir_path. This creates a leaner jar file. If BLD files
  # are written properly, then this would not be a major performance issue. In
  # most cases inclusion and exclusion rules would be specified only in build
  # rules that import trimmed external dependencies in the system.
  cleanup_depth = 0
  while True:
    cleanup_depth += 1
    assert cleanup_depth <= MAX_CLEANUP_DEPTH
    empty_dirs = _get_all_empty_dirs(dir_path)
    if not empty_dirs:
      break
    for empty_dir in empty_dirs:
      _check_and_remove(empty_dir)


def _get_error_text(clashing_classes, current_jar, class_jar_dict):
  """Error text when jars have non-benign version conflict."""
  clashing_classes = sorted(clashing_classes)
  if len(clashing_classes) > MAX_DEBUG_LEN:
    clashing_classes = clashing_classes[:MAX_DEBUG_LEN]
  text_fields = ['Cannot merge clashing jar files:']
  clashing_jars = list(set([class_jar_dict[cc] for cc in clashing_classes]))
  clashing_jars = sorted(clashing_jars)
  for clashing_jar in clashing_jars:
    text_fields.append('\t' + su.log_normalize(clashing_jar))
  text_fields.extend([
      '\t -->' + su.log_normalize(current_jar),
      'Clashing class examples:',
      '\t' + '\n\t'.join(clashing_classes)])
  return '\n'.join(text_fields)


def _real_new_files(all_files_with_sig, new_files_with_sig):
  """Remove common files from new files list and return exclusive new list."""
  common_files = [f for f in new_files_with_sig if f in all_files_with_sig]
  return [f for f in new_files_with_sig if f not in common_files]


def _ensure_no_repetition(jar_files, inclusions, exclusions, jar_out_file):
  """Make sure that there are no repetitions in the jars."""
  orig_dir = os.getcwd()
  temp_dir = _get_temp_dir(jar_out_file, 'no_rep')
  os.chdir(temp_dir)
  all_files_with_sig = []
  class_jar_dict = {}
  try:
    count = len(jar_files)
    for index in xrange(count):
      dir_path = os.path.join(temp_dir, str(index))
      os.makedirs(dir_path)
      os.chdir(dir_path)
      subprocess.check_call([su.JAR_BIN, 'xf', jar_files[index]])
      if os.path.exists(su.JAR_MANIFEST_PATH):
        shutil.rmtree(su.JAR_MANIFEST_PATH)
      _do_cleanup('.', inclusions, exclusions)
      new_files_with_sig = _real_new_files(all_files_with_sig,
                                           _get_all_files_in_dir('.'))
      repeated_files = [
          f[0] for f in new_files_with_sig if f[0] in class_jar_dict]
      if repeated_files:
        raise Error(
            _get_error_text(repeated_files, jar_files[index], class_jar_dict))
      all_files_with_sig.extend(new_files_with_sig)
      for new_file in new_files_with_sig:
        class_jar_dict[new_file[0]] = jar_files[index]
  finally:
    shutil.rmtree(temp_dir)
  os.chdir(orig_dir)


def _merge_jars(jar_files, inclusions, exclusions, main_class, jar_out_file):
  """Make sure that there are no repetitions in the jars."""
  need_main = (main_class != su.JAVA_FAKE_MAIN_CLASS)
  # No need for complicated linking under certain conditions.
  copy_ok = ((not need_main) and (1 == len(jar_files)) and
             (not inclusions) and (not exclusions))
  if copy_ok:
    subprocess.check_call(
        su.get_copy_command(
            jar_files[0], jar_out_file,
            jar_out_file.startswith(su.BUILD_WORK_DIR + os.sep)))
    return
  orig_dir = os.getcwd()
  temp_dir = _get_temp_dir(jar_out_file, 'final')
  os.chdir(temp_dir)
  try:
    for jar_file in jar_files:
      subprocess.check_call([su.JAR_BIN, 'xf', jar_file])
      _check_and_remove(su.JAR_MANIFEST_PATH)
    _do_cleanup('.', inclusions, exclusions)
    _check_and_remove(jar_out_file)
    if need_main:
      merge_command = [su.JAR_BIN, 'cfe', jar_out_file, main_class]
    else:
      merge_command = [su.JAR_BIN, 'cf', jar_out_file]
    merge_command.extend(os.listdir('.'))
    subprocess.check_call(merge_command)
  finally:
    shutil.rmtree(temp_dir)
  os.chdir(orig_dir)


def do_merge(lib_details, jar_out_file, main_class):
  """Merge jar files."""
  inclusions, exclusions, jar_files = lib_details
  assert all([su.path_exists(f) for f in jar_files])
  assert su.path_exists(os.path.dirname(jar_out_file))
  assert 1 <= len(jar_files)
  if len(jar_files) > 1:
    # Though this is double work, it is good to do this for health of code. We
    # need to make sure we know that there is exactly one way to get an
    # implementation in the file.
    _ensure_no_repetition(jar_files, inclusions, exclusions, jar_out_file)
  _merge_jars(jar_files, inclusions, exclusions, main_class, jar_out_file)
