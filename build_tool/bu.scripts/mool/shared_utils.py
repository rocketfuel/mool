"""Implement common utilities."""
import fcntl
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import urllib
import zipfile

from collections import OrderedDict

CACHE_FILE_NAME = '.project.cache'
COMMENT_CHAR = '#'
DIR_ROOT_KEY = 'dir_root'
LOCK_FILE_NAME = '.bu.lock'
QUOTE_CHAR = '"'
RULE_KEY = 'build_rules'

# These environment variables are always required.
BU_SCRIPT_DIR = os.environ['BU_SCRIPT_DIR']
BUILD_ROOT = os.environ['BUILD_ROOT']
BUILD_OUT_DIR = os.environ['BUILD_OUT_DIR']
BUILD_WORK_DIR = os.environ['BUILD_WORK_DIR']

# These environment variables are required when they are used in projects.
# Hence we specify harmless defaults.
BOOST_INSTALL_DIR = os.environ.get('BOOST_DIR', '/dev/null')
CC_COMPILER = os.environ.get('CC_COMPILER', 'false')
CC_INSTALL_PREFIX = os.environ.get('CC_INSTALL_PREFIX', '/dev/null')
THRIFT_INSTALL_DIR = os.environ.get('THRIFT_DIR', '/dev/null')
JAR_SEARCH_PATH = os.environ.get('JAR_SEARCH_PATH', '/dev/null')
JAVA_DEFAULT_VERSION = os.environ.get('JAVA_DEFAULT_VERSION', 'false')
JAVA_HOME = os.environ.get('JAVA_HOME', '/dev/null')
JAVA_PROTOBUF_JAR = os.environ.get('JAVA_PROTOBUF_JAR', '/dev/null')
JAVA_TEST_DEFAULT_JARS = [
    j for j in os.environ.get('JAVA_TEST_DEFAULT_JARS', '').split(' ') if j]
JAVA_THRIFT_JARS = [
    j for j in os.environ.get('JAVA_THRIFT_JARS', '/dev/null').split(' ') if j]
PEP8_BINARY = os.environ.get('PEP8_BINARY', '/dev/null')
PEP8_COMMAND_LINE = PEP8_BINARY.split()
PROTO_COMPILER = os.environ.get('PROTO_COMPILER', '/dev/null')
PYLINT_RC_FILE = os.environ.get('PYLINT_RC_FILE', '/dev/null')
SCALA_DEFAULT_VERSION = os.environ.get('SCALA_DEFAULT_VERSION', 'false')
SUBMITQ_DEBUG_MODE = os.environ.get('SUBMITQ_DEBUG_MODE', '').lower() == 'true'
SUBMIT_QUEUE_FILE_NAME = 'SUBMITQ'
THRIFT_COMPILER = os.environ.get('THRIFT_COMPILER', '/dev/null')
DEVELOPER_MODE = os.environ.get('DEVELOPER_MODE', 'false')
MAVEN_PREFER_LOCAL_REPO = os.environ.get('MAVEN_PREFER_LOCAL_REPO', '')

CC_BOOST_INCDIR = os.path.join(BOOST_INSTALL_DIR, 'include')
CC_BOOST_LIBDIR = os.path.join(BOOST_INSTALL_DIR, 'lib')
CC_THRIFT_INCDIR = os.path.join(THRIFT_INSTALL_DIR, 'include')
CC_THRIFT_LIBDIR = os.path.join(THRIFT_INSTALL_DIR, 'lib')
CC_PROTOBUF_INCDIR = os.path.join(CC_INSTALL_PREFIX, 'include')
CC_PROTOBUF_LIBDIR = os.path.join(CC_INSTALL_PREFIX, 'lib')

# These constants are functionally dependent on the previous set of
# environment variables.
MOOL_SRC_DIR = os.path.join(BU_SCRIPT_DIR, 'mool')
DUMMY_CC = os.path.join(MOOL_SRC_DIR, 'dummy.cc')
JAR_BIN = os.path.join(JAVA_HOME, 'bin', 'jar')
JAVA_COMPILER = os.environ.get('JAVA_COMPILER',
                               os.path.join(JAVA_HOME, 'bin', 'javac'))
JAVA_RUNTIME = os.path.join(JAVA_HOME, 'bin', 'java')

ALL_DEP_PATHS_KEY = 'all_dependency_paths'
ALL_DEPS_KEY = '_all_deps'
ALL_LIGHT_RULES_KEY = 'LIGHTRULES'
ALL_RULES_KEY = 'ALL'
ALL_SRCS_KEY = 'all_sources_key'
ARCHIVE_TYPE = 'archive_type'
BUILD_FILE_NAME = 'BLD'
CC_BIN_TYPE = 'cc_bin'
CC_LIB_TYPE = 'cc_lib'
CC_PROTO_LIB_TYPE = 'cc_proto_lib'
CC_TEST_TYPE = 'cc_test'
CC_THRIFT_LIB_TYPE = 'cc_thrift_lib'
CHANGE_CURR_DIR = 'chdir'
COMPILE_COMMAND_KEY = 'compile_command'
COMPILE_DEPS_KEY = 'compileDeps'
COMPILE_IGNORE_WARNINGS_KEY = 'ignore_compiler_warnings'
COMPILE_LIBS_KEY = 'compile_libs'
COMPILE_PARAMS_KEY = 'compile_params'
CREATE_ARCHIVE_ALL_CURRDIR = 'create_archive_all_currdir'
DEFAULT_FILE_COLL_ARCHIVE_TYPE = 'jar'
DEPS_KEY = 'deps'
DOWNLOAD_CHUNK_SIZE = 1024
EXPORT_MVN_DEPS = 'export_mvn_deps'
EXPORTED_MVN_DEPS_FILE_KEY = 'exported_mvn_deps_file_key'
EXTRACT_ARCHIVE_IN_CURRDIR = 'extract_archive_in_currdir'
EXTRACT_IN_ZIP = 'extract_in_zip'
EXTRACT_RESOURCES_DEP_KEY = 'extract_deps'
FILE_COLL_TYPE = 'file_coll'
FILE_PACKAGE_KEY = 'file_package'
FILE_COLL_DEPS_KEY = 'file_coll_deps'
HDRS_KEY = 'hdrs'
JAR_INCLUDE_KEY = 'jar_include_paths'
JAR_MANIFEST_KEY = 'META-INF'
JAR_MANIFEST_SERVICE_KEY = 'services'
JAR_MANIFEST_PATH = os.path.join('.', JAR_MANIFEST_KEY)
JAR_EXCLUDE_KEY = 'jar_exclude_paths'
JAVA_BIN_TYPE = 'java_bin'
JAVA_FAKE_MAIN_CLASS = 'java_fake_main_class'
JAVA_LIB_TYPE = 'java_lib'
JAVA_LINK_JAR_COMMAND = 'java_link_jar'
JAVA_TESTNG_RUNNER = 'java_testng_runner'
JAVA_OUTER_CLASSNAME_KEY = 'java_outer_classname'
JAVA_PACKAGE_KEY = 'java_package'
JAVA_PROTO_LIB_TYPE = 'java_proto_lib'
JAVA_PROTO_LINK_LIBS_KEY = 'java_proto_link_libs'
JAVA_TEST_TYPE = 'java_test'
JAVA_TESTNG_GROUPS = 'test_groups'
JAVA_TESTNG_ROOT = 'org.testng.TestNG'
JAVA_THRIFT_LIB_TYPE = 'java_thrift_lib'
JAVA_VERSION_KEY = 'java_version'
JAVAC_OUTDIR_KEY = 'javac_outdir_key'
LINK_COMMANDS_KEY = 'link_commands'
LINK_INCLUDE_DEPS_KEY = 'includeDeps'
LINK_LIBS_KEY = 'link_libs'
MAIN_CLASS_KEY = 'main_class'
MAIN_METHOD_KEY = 'main_method'
MAVEN_ARTIFACT_ID_KEY = 'artifact_id'
MAVEN_CLASSIFIER_KEY = 'classifier'
MAVEN_DEPS_KEY = 'maven_deps'
MAVEN_GROUP_ID_KEY = 'group_id'
MAVEN_IDENTIFIERS_KEY = 'maven_id'
MAVEN_REPO_URL_KEY = 'repo_url'
MAVEN_SPECS_KEY = 'maven_specs'
MAVEN_VERSION_KEY = 'version'
NAME_KEY = 'rule_name'
OTHER_INCLUDE_DIRS = 'incdirs'
OTHER_LIB_DIRS = 'libdirs'
OUT_CC_KEY = 'out_cc_key'
OUTDIR_KEY = 'outdir_key'
OUT_HEADER_KEY = 'out_header_key'
OUT_KEY = 'out_key'
PACKAGE_MODULES_KEY = 'package_modules'
PACKAGE_TESTS_KEY = 'package_tests'
PATH_KEY = 'rule_path'
PATH_SUBDIR_KEY = 'path_subdir'
PC_DEPS_KEY = 'precompiled_deps'
PC_DEPS_PREFIX = 'env.'
PERFORM_JAVA_LINK_ALL_CURRDIR = 'perform_java_link_all_currdir'
POSSIBLE_PREFIXES_KEY = 'possible_prefixes'
PRECOMPILE_COMMANDS_KEY = 'precompile_commands'
PROTO_OUTDIR_KEY = 'proto_outdir_key'
PROTO_SRCS_KEY = 'proto_sources_key'
PYTHON_BIN_TYPE = 'py_bin'
PYTHON_COMPILE_ALL_CURRDIR = 'python_compile_all_currdir'
PYTHON_CREATE_INITIALIZERS = 'python_create_initializers'
PYTHON_EXPAND_LIB = 'python_expand_lib'
PYTHON_FAKE_MAIN_METHOD = 'py.fake.main.method'
PYTHON_LINK_ALL = 'python_link_all'
PYTHON_LIB_TYPE = 'py_lib'
PYTHON_PROTO_LIB_TYPE = 'py_proto_lib'
PYTHON_THRIFT_LIB_TYPE = 'py_thrift_lib'
PYTHON_SKIPLINT_KEY = 'py_skiplint'
PYTHON_TEST_TYPE = 'py_test'
RELEASE_PACKAGE_TYPE = 'release_package'
RELEASE_TEST_COMMANDS_KEY = 'release_test_commands'
RULE_FILE_PATH = 'rule_file_path'
RULE_NORMALIZED_KEY = 'is_normalized'
RULE_ROOT_NAME = 'mool'
RULE_SEPARATOR = '.'
RULE_WEIGHT_KEY = 'weight'
RUNTIME_PARAMS_KEY = 'runtime_params'
SCALA_BIN_TYPE = 'scala_bin'
SCALA_LIB_TYPE = 'scala_lib'
SCALA_LINK_JAR_COMMAND = 'scala_link_jar'
SCALA_PACKAGE_KEY = 'scala_package'
SCALA_TEST_TYPE = 'scala_test'
SCALA_TESTNG_GROUPS = 'test_groups'
SCALA_VERSION_KEY = 'scala_version'
SRCS_KEY = 'srcs'
SYMBOL_KEY = 'rule_symbol'
SYS_DEPS_KEY = 'sys_deps'
TEMP_OUT_KEY = 'temp_output'
THRIFT_SERVICES_KEY = 'thrift_services'
VALGRIND_PREFIX = os.environ.get('VALGRIND_PREFIX', '').split()

TEST_CLASS_KEY = 'test_class'
TEST_CLASSES_KEY = 'test_classes'
TEST_COMMANDS_KEY = 'test_command_list'
TEST_MODE_EXECUTION = False
TYPE_KEY = 'rule_type'
WDIR_KEY = 'wdir_key'
WDIR_CLSDEPS_KEY = 'wdir_clsdeps_key'
WDIR_SRC_KEY = 'wdir_src_key'
WDIR_TARGET_KEY = 'wdir_target_key'

TRUE_REPR = 'true'
FALSE_REPR = 'false'

BUILD_RULE_PREFIX = '{}{}'.format(RULE_ROOT_NAME, RULE_SEPARATOR)
PROGRESS_BAR = '\rDownload: [{}{}] {:>3}%'
PROGRESS_BAR_SIZE = 50

#======= Keys used to refer to function names in other modules.  =========#
MERGE_CPP_SOURCE_FILES = 'MERGE_CPP_SOURCE_FILES'
PYTHON_PYLINT_CHECK = 'PYTHON_PYLINT_CHECK'
THRIFT_CHECK_GENERATED_SOURCE = 'THRIFT_CHECK_GENERATED_SOURCE'
THRIFT_COMPILE_GENERATED_JAVA = 'THRIFT_COMPILE_GENERATED_JAVA'


#================  Keys used in rule_details dictionary.  ================#

# (str) For referring to final out headers directory in thrift cc lib rule.
OUT_HEADERS_DIR_KEY = 'OUT_HEADERS_DIR_KEY'
# (list) Full path to all the generated headers are added to this key.
OUT_HEADERS_KEY = 'OUT_HEADERS_KEY'


class Error(Exception):
  """Generic error class for mool.
  All other modules should use this as base class."""


def print_rule_details_debug(rule_details):
  """Emit rule details."""
  def _emit_items(item):
    """Emit items."""
    if isinstance(item, str):
      return log_normalize(item)
    elif isinstance(item, list):
      return [_emit_items(x) for x in item]
    else:
      assert False

  for key, value in globals().iteritems():
    if isinstance(value, str) and value in rule_details:
      print '{:25}: {}'.format(key, _emit_items(rule_details[value]))
  print
  print


def get_epoch_milliseconds():
  """Get milliseconds since Unix epoch."""
  return int(time.time() * 1000)


def child_contained_in(child, parent):
  """Checks if a child directory is somewhere deep inside parent."""
  parent = os.path.join(os.path.realpath(parent), '')
  child = os.path.join(os.path.realpath(child), '')
  return child.startswith(parent)


def is_temporary_path(item_path):
  """Checks if file or directory is temporary (safe to delete)."""
  return ((child_contained_in(item_path, BUILD_OUT_DIR)) or
          (child_contained_in(item_path, BUILD_WORK_DIR)))


def cleandir(dir_path):
  """Clean and create directory."""
  assert is_temporary_path(dir_path)
  assert os.path.realpath(dir_path) != os.path.realpath(os.path.curdir)
  if path_exists(dir_path):
    shutil.rmtree(dir_path)
  os.makedirs(dir_path)


def createdir(dir_path, clean=False):
  """Create a given directory and optionally clean an existing one."""
  assert is_temporary_path(dir_path)
  if not path_exists(dir_path):
    os.makedirs(dir_path)
  elif clean:
    cleandir(dir_path)


def download_cached_item(url, file_path):
  """Download url to file path."""
  if path_exists(file_path):
    return

  def report_hook(count, block_size, total_size):
    """Handler for urllib report hook."""
    if total_size <= 0:
      # Ignore progress bar for non-existent links. Currently used in
      # development mode for downloading source jars.
      return
    bar_size = PROGRESS_BAR_SIZE
    done = min((block_size * count * bar_size / total_size), bar_size)
    print PROGRESS_BAR.format('=' * done, ' ' * (bar_size - done), done * 2),
    sys.stdout.flush()

  subprocess.check_call(get_mkdir_command(os.path.dirname(file_path)))
  temp_path = file_path + '.temp'
  try:
    logging.debug('Downloading file from %s.', url)
    opener = urllib.URLopener()
    opener.retrieve(url, temp_path, reporthook=report_hook)
    print
  except IOError as exc:
    logging.error('Download from %s failed!', url)
    raise exc
  shutil.move(temp_path, file_path)


def init_rule_common(rule_details, out_file, expansion_list):
  """Initialize common properties of a build rule."""
  assert rule_details[DIR_ROOT_KEY].startswith(BUILD_ROOT)
  path_subdir = os.sep.join(rule_details[PATH_KEY].split(RULE_SEPARATOR)[1:])
  rule_details[WDIR_KEY] = os.path.join(BUILD_WORK_DIR, path_subdir,
                                        rule_details[NAME_KEY])
  rule_details[OUTDIR_KEY] = os.path.join(BUILD_OUT_DIR, path_subdir)
  rule_details[PATH_SUBDIR_KEY] = path_subdir
  if out_file:
    rule_details[OUT_KEY] = os.path.join(rule_details[OUTDIR_KEY], out_file)
  for key in expansion_list:
    rule_details[key] = [os.path.join(rule_details[DIR_ROOT_KEY], f)
                         for f in rule_details.get(key, [])]


def set_workdir_child(rule_details, path_key, extension):
  """Set a working directory child path property for a build rule."""
  rule_details[path_key] = os.path.join(rule_details[WDIR_KEY], extension)


def get_proto_compile_command(rule_details, out_path):
  """Get the protoc command line for specified parameters."""
  assert 1 == len(rule_details[SRCS_KEY])
  if CC_PROTO_LIB_TYPE == rule_details[TYPE_KEY]:
    language = 'cpp_out'
  elif JAVA_PROTO_LIB_TYPE == rule_details[TYPE_KEY]:
    language = 'java_out'
  elif PYTHON_PROTO_LIB_TYPE == rule_details[TYPE_KEY]:
    language = 'python_out'
  else:
    assert False
  src_file = get_relative_path(rule_details[POSSIBLE_PREFIXES_KEY],
                               rule_details[SRCS_KEY][0])
  compile_command = PROTO_COMPILER.split()
  compile_command.append('--proto_path=.')
  compile_command.append('--{}={}'.format(language, out_path))
  compile_command.append(src_file)
  return compile_command


def path_exists(file_path):
  """Shim for os.path.exists that can be mocked during tests."""
  return os.path.exists(file_path)


def path_isfile(file_path):
  """Shim for os.path.isfile that can be mocked during tests."""
  return os.path.isfile(file_path)


def expand_env_vars(dep_path):
  """Retrieve dependency file path by expanding environment variables."""
  # TODO: Merge logic of _expand_env_vars_if_needed in this function.
  path_parts = dep_path.split(os.sep)
  env_var = path_parts[0]
  assert env_var.startswith(PC_DEPS_PREFIX)
  path_parts[0] = os.environ[env_var[len(PC_DEPS_PREFIX):]]
  result = os.sep.join(path_parts)
  assert path_exists(result)
  return result


def get_mkdir_command(dir_path):
  """Get command line for making a directory."""
  return ['mkdir', '-p', dir_path]


def prefix_transform(possible_prefixes):
  """Apply common transforms to list of possible_prefixes."""
  possible_prefixes.append(BUILD_ROOT)
  possible_prefixes = sorted(list(set(possible_prefixes)))
  assert all([(not p.endswith(os.sep)) for p in possible_prefixes])
  return [p + os.sep for p in possible_prefixes]


def find_all_bld_files(path):
  """Search BLD files recursively."""
  bld_files = []
  for root, _, filenames in os.walk(os.path.abspath(path)):
    if BUILD_FILE_NAME in filenames:
      bld_files.append(os.path.join(root, BUILD_FILE_NAME))
  return bld_files


def get_relative_path(possible_prefixes, file_path):
  """Get the relative path of a file name."""
  if DUMMY_CC == file_path:
    return file_path
  assert all([(p.endswith(os.sep)) for p in possible_prefixes])
  for prefix in sorted(possible_prefixes, reverse=True):
    if file_path.startswith(prefix):
      return '.{}{}'.format(os.sep, file_path[len(prefix):])
  logging.error('Could not get relative path for: %s', file_path)
  for prefix in possible_prefixes:
    logging.error('Candidate prefix: %s', prefix)
  assert False


def get_copy_command(src_file, dst_file, use_links):
  """Get the 'copy' command. Sometimes linking can be more efficient."""
  copy_command = ['ln', '-f', '-s'] if use_links else ['cp']
  copy_command.extend([src_file, dst_file])
  return copy_command


def cp_commands_list(rule_details, command_key, use_links=True):
  """Get command list to copy a list of files from source to work directory."""
  dst_dir_list = []
  possible_prefixes = rule_details[POSSIBLE_PREFIXES_KEY]

  def _cp_commands(src_file):
    """Get commands to copy or link a file from source to work directory."""
    # File linking is more efficient than copying.
    dst_file = get_relative_path(possible_prefixes, src_file)
    dst_dir = os.path.dirname(dst_file)
    copy_command = get_copy_command(src_file, dst_file, use_links)
    result = []
    if dst_dir not in dst_dir_list:
      result.append(get_mkdir_command(dst_dir))
      dst_dir_list.append(dst_dir)
    result.append(copy_command)
    return result

  command_list = []
  for fname in rule_details[command_key]:
    if fname == DUMMY_CC:
      continue
    command_list.extend(_cp_commands(fname))
  return command_list


def log_normalize(file_path):
  """Normalize the logged value of a file path."""
  file_path = file_path.replace(BUILD_OUT_DIR, '${BUILD_OUT_DIR}')
  file_path = file_path.replace(BUILD_WORK_DIR, '${BUILD_WORK_DIR}')
  file_path = file_path.replace(BUILD_ROOT, '${BUILD_ROOT}')
  return file_path


def lock_working_dir():
  """Lock the working directory to enforce single instance of script."""
  lock_file = os.path.join(BUILD_WORK_DIR, LOCK_FILE_NAME)
  file_object = open(lock_file, 'w')
  fcntl.lockf(file_object, fcntl.LOCK_EX)
  return file_object


def release_working_dir(file_object):
  """Release the working directory to enforce single instance of script."""
  if not file_object:
    return
  fcntl.lockf(file_object, fcntl.LOCK_UN)
  file_object.close()


def read_file(file_path):
  """Read text from file."""
  with open(file_path, 'rb') as file_object:
    return file_object.read()


def write_file(file_path, file_text):
  """Write text to file."""
  with open(file_path, 'wb') as file_object:
    file_object.write(file_text)


def read_build_file(file_path):
  """Read build rules from file."""
  def _ascii_encoder(obj):
    """Convert UNICODE strings to ASCII recursively."""
    if isinstance(obj, dict):
      obj = OrderedDict(sorted([(k.encode('ascii'), _ascii_encoder(v))
                                for (k, v) in obj.iteritems()]))
    elif isinstance(obj, list):
      obj = [_ascii_encoder(i) for i in obj]
    elif isinstance(obj, unicode):
      obj = obj.encode('ascii')
    else:
      assert isinstance(obj, str)
    return obj

  # Converts the concealed JSON file to a real JSON file and then loads it in
  # memory as a JSON dictionary.
  lines = read_file(file_path).split('\n')
  lines = [l.strip() for l in lines]
  lines = [l for l in lines if not l.startswith(COMMENT_CHAR)]
  lines = '\n'.join(lines)
  lines = '{}{}{}{}{}'.format('{"', RULE_KEY, '": {', lines, '}}')
  try:
    return json.loads(lines, object_hook=_ascii_encoder)[RULE_KEY]
  except ValueError:
    raise Error('Invalid JSON in file {}'.format(file_path))


def string_to_bool(text):
  """Converts a string representation of a bool to a bool."""
  text = text.lower()
  assert text in [TRUE_REPR, FALSE_REPR]
  return text == TRUE_REPR


def _get_current_snapshot_text(file_list, rule_hash):
  """Gets current snapshot text from file list."""
  def _file_signature(file_path):
    """Gets the textual signature of a file version on disk."""
    mod_timestamp = int(1000 * os.path.getmtime(file_path))
    size_bytes = os.stat(file_path).st_size
    return str((mod_timestamp, size_bytes))

  found_all = True
  curr_snapshot_map = {}
  for file_path in file_list:
    assert file_path not in curr_snapshot_map
    if not path_exists(file_path):
      logging.debug('Did not find %s', file_path)
      found_all = False
      break
    curr_snapshot_map[file_path] = _file_signature(file_path)
  curr_snapshot_text = '\n'.join(
      ['{} {}'.format(v, k) for (k, v) in curr_snapshot_map.iteritems()])
  full_snapshot_text = '{}: {}\n{}'.format(
      'RULE_DETAILS_HASH_VALUE', rule_hash, curr_snapshot_text)
  return found_all, full_snapshot_text


def needs_build(working_dir, file_list, rule_hash):
  """Checks file list snapshot for any changes."""
  tracer = logging.debug
  cache_file = os.path.join(working_dir, CACHE_FILE_NAME)
  if not path_exists(cache_file):
    tracer('Did not find cache file at %s', log_normalize(cache_file))
    return True
  found_all, snapshot_text = _get_current_snapshot_text(file_list, rule_hash)
  if not found_all:
    tracer('Did not find all files present.')
    return True
  cached_text = read_file(cache_file)
  if snapshot_text != cached_text:
    tracer('Snapshot mismatch.')
    tracer('\nCache file: \n%s', cached_text)
    tracer('\nCurrent snapshot: \n%s', snapshot_text)
    return True
  return False


def save_file_list_cache(working_dir, file_list, rule_hash):
  """Saves file list snapshot to disk."""
  found_all, snapshot_text = _get_current_snapshot_text(file_list, rule_hash)
  assert found_all
  cache_file = os.path.join(working_dir, CACHE_FILE_NAME)
  write_file(cache_file, snapshot_text)


def check_dirname(dir_name):
  """Check directory name."""
  assert os.path.isdir(dir_name)
  assert dir_name == os.path.abspath(dir_name)


def change_dir(dir_name_params):
  """Change directory command."""
  assert 1 == len(dir_name_params)
  os.chdir(dir_name_params[0])


def get_javac_bin(version):
  """Adds required command line arguments to javac command."""
  java_home = os.environ.get('JAVA_HOME', False)
  if not java_home:
    raise Error('JAVA_HOME environment variable not set!')
  bootclasspath = os.path.join(JAVA_HOME, 'jre', 'lib', 'rt.jar')
  default_cmd = os.environ.get('JAVA_COMPILER',
                               os.path.join(JAVA_HOME, 'bin', 'javac'))
  javac_cmd = ('{} -source {} -target {} -bootclasspath {}'.format(
               default_cmd, version, version, bootclasspath))
  return javac_cmd


def get_scala_home(version):
  """Returns path to scala home for given version."""
  modified_version = version.replace('.', '_')
  scala_home = os.environ.get('SCALA_HOME_{}'.format(modified_version), False)
  if not scala_home:
    raise Error('SCALA_HOME not set for version {}!'.format(version))
  return scala_home


def get_scala_compiler(version):
  """Return scala compiler binary for given version."""
  return os.path.join(get_scala_home(version), 'bin', 'scalac')


def get_scala_runtime(version):
  """Return scala runtime binary for given version."""
  return os.path.join(get_scala_home(version), 'bin', 'scala')


def get_affected_rules(changed_files_list):
  """Get list of affected rules from list of changed files."""
  submitq_rules_dict = {}
  build_root_with_sep = os.path.join(BUILD_ROOT, '')
  prefix_len = len(build_root_with_sep)

  def _load_file_rules(submitq_file_path):
    """Reads a SUBMITQ file into cache, and returns the values."""
    if not submitq_file_path in submitq_rules_dict:
      if not path_exists(submitq_file_path):
        submitq_rules_dict[submitq_file_path] = []
      else:
        file_lines = [r.strip()
                      for r in read_file(submitq_file_path).split('\n')
                      if r.strip()]
        # SUBMITQ files do not support relative rule paths.
        assert all([not r.startswith(RULE_SEPARATOR) for r in file_lines])
        submitq_rules_dict[submitq_file_path] = [
            r for r in file_lines if r.startswith(BUILD_RULE_PREFIX)]
    return submitq_rules_dict[submitq_file_path]

  def _get_submitq_rules(file_path):
    """Get submitq rules for a file path.

    Note that it is possible that a certain file does not have any associated
    submit queue tests.
    """
    assert not file_path.endswith(os.sep)
    result = []
    while True:
      file_dir = os.path.dirname(file_path)
      if file_dir.endswith(os.sep):
        break
      if not file_dir.startswith(build_root_with_sep):
        break
      result.extend(
          _load_file_rules(os.path.join(file_dir, SUBMIT_QUEUE_FILE_NAME)))
      if path_exists(os.path.join(file_dir, BUILD_FILE_NAME)):
        result.append('{}{}{}{}'.format(
            BUILD_RULE_PREFIX,
            file_dir[prefix_len:].replace(os.sep, RULE_SEPARATOR),
            RULE_SEPARATOR, ALL_LIGHT_RULES_KEY))
      file_path = file_dir
    return result

  affected_rules = []
  for file_path in changed_files_list:
    affected_rules.extend(_get_submitq_rules(file_path))
  return sorted(list(set(affected_rules)))


def is_developer_mode():
  """Returns true if mool set to run in developer mode."""
  return DEVELOPER_MODE.strip().lower() == 'true'


def _force_jar_extract_cwd(jar_path):
  """Forcefully extracts the jar to current working directory. It resolves the
  filename collisions on case insensitive file system and skips those files
  with a warning."""
  curdir = os.path.abspath('.')

  def _manual_unzip_to_cwd(jar_file):
    """Unzip each file manually if the file at same path doesn't exist."""
    with zipfile.ZipFile(jar_file, 'r') as zipfile_obj:
      all_files = sorted(zipfile_obj.namelist())
      for name in all_files:
        lower_name = name.lower().rstrip('/')
        full_path = os.path.join(curdir, lower_name)
        if os.path.exists(lower_name) or os.path.isdir(lower_name):
          logging.debug('Skipping %s, file/directory already exists!', name)
        elif not os.path.isdir(os.path.dirname(full_path)):
          logging.debug('File with name %s exists, cannot extract %s!',
                        log_normalize(os.path.dirname(full_path)), name)
        else:
          zipfile_obj.extract(name)

  try:
    subprocess.check_output(
        [JAR_BIN, 'xf', jar_path], stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as exc:
    msg = exc.output
    if 'sun.tools.jar.Main.extractFile' in msg and (
       'could not create directory' in msg or '(Is a directory)' in msg):
      logging.warn('Forcefully extracting %s in %s!',
                   log_normalize(jar_path), log_normalize(curdir))
      _manual_unzip_to_cwd(jar_path)
    else:
      raise exc


def extract_all_currdir(jar_path, delete_manifest=True):
  """Extracts the given jar into current directory and deletes manifest
  files."""
  # Minor check to confirm it is a valid zip so that 404-downloads from urllib
  # does not prevent the build success.
  # TODO: Add md5 verification logic after jar download so that this
  # verification is not needed everytime before using the jar.
  with zipfile.ZipFile(jar_path, 'r') as zip_obj:
    zip_obj.testzip()

  _force_jar_extract_cwd(jar_path)
  if delete_manifest and os.path.exists(JAR_MANIFEST_PATH):
    shutil.rmtree(JAR_MANIFEST_PATH)


def report_timing(func):
  """Decorator function for capturing function execution timing."""
  def profileit(*args):
    """Profiler function to capture execution time."""
    time1 = time.time()
    ret = func(*args)
    time2 = time.time()
    elapsed = (time2 - time1) * 1000.0
    logging.debug('%s function took %0.3f ms.', func.func_name, elapsed)
    return ret
  return profileit


def get_rule_symbol(bld_file_path, build_root, rule_name):
  """Returns full rule symbol w.r.t to build_root."""
  rel_path = os.path.relpath(
      os.path.realpath(bld_file_path), os.path.realpath(build_root)).rstrip(
          BUILD_FILE_NAME).replace('/', RULE_SEPARATOR)
  return '{}{}{}{}'.format(RULE_ROOT_NAME, RULE_SEPARATOR, rel_path, rule_name)


def get_dictionary_hash(python_dict):
  """Returns hash of a python dictionary."""
  return json.dumps(python_dict, sort_keys=True).__hash__()


def grep_lines_in_file(file_path, pattern_str):
  """Python re module based pattern matching and returns list of tuples with
  line and set of matching groups. """
  pattern = re.compile(pattern_str)
  with open(file_path, 'r') as file_obj:
    for line in file_obj:
      match = pattern.match(line)
      if match:
        yield (match.group(), match.groups())
