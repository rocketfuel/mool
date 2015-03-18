"""Implement common utilities."""
import fcntl
import json
import logging
import os
import shutil
import subprocess
import time
import urllib2

CACHE_FILE_NAME = '.project.cache'
COMMENT_CHAR = '#'
DIR_ROOT_KEY = 'dir_root'
LOCK_FILE_NAME = '.bu.lock'
RULE_KEY = 'build_rules'

# These environment variables are always required.
BU_SCRIPT_DIR = os.environ['BU_SCRIPT_DIR']
BUILD_ROOT = os.environ['BUILD_ROOT']
BUILD_OUT_DIR = os.environ['BUILD_OUT_DIR']
BUILD_WORK_DIR = os.environ['BUILD_WORK_DIR']

# These environment variables are required when they are used in projects.
# Hence we specify harmless defaults.
CC_COMPILER = os.environ.get('CC_COMPILER', 'false')
GMOCK_DIR = os.environ.get('GMOCK_DIR', '/dev/null')
GTEST_DIR = os.environ.get('GTEST_DIR', '/dev/null')
JAR_SEARCH_PATH = os.environ.get('JAR_SEARCH_PATH', '/dev/null')
JAVA_DEFAULT_VERSION = os.environ.get('JAVA_DEFAULT_VERSION', 'false')
JAVA_HOME = os.environ.get('JAVA_HOME', '/dev/null')
JAVA_PROTOBUF_JAR = os.environ.get('JAVA_PROTOBUF_JAR', '/dev/null')
JAVA_TEST_DEFAULT_JARS = [
    f.strip()
    for f in os.environ.get('JAVA_TEST_DEFAULT_JARS', '').split() if f.strip()]
PEP8_BINARY = os.environ.get('PEP8_BINARY', 'false')
PEP8_COMMAND_LINE = PEP8_BINARY.split()
PROTO_COMPILER = os.environ.get('PROTO_COMPILER', 'false')
PYLINT_RC_FILE = os.environ.get('PYLINT_RC_FILE', '/dev/null')
SCALA_DEFAULT_VERSION = os.environ.get('SCALA_DEFAULT_VERSION', 'false')
SUBMITQ_DEBUG_MODE = os.environ.get('SUBMITQ_DEBUG_MODE', '').lower() == 'true'
SUBMIT_QUEUE_FILE_NAME = 'SUBMITQ'
DEVELOPER_MODE = os.environ.get('DEVELOPER_MODE', 'false')


# These constants are functionally dependent on the previous set of
# environment variables.
MOOL_SRC_DIR = os.path.join(BU_SCRIPT_DIR, 'mool')
DUMMY_CC = os.path.join(MOOL_SRC_DIR, 'dummy.cc')
JAR_BIN = os.path.join(JAVA_HOME, 'bin', 'jar')
JAR_TESTER_SCRIPT = os.path.join(MOOL_SRC_DIR, 'jar_testng_runner.py')
JAVA_COMPILER = os.environ.get('JAVA_COMPILER',
                               os.path.join(JAVA_HOME, 'bin', 'javac'))
JAVA_RUNTIME = os.path.join(JAVA_HOME, 'bin', 'java')

ALL_DEP_PATHS_KEY = 'all_dependency_paths'
ALL_DEPS_KEY = '_all_deps'
ALL_LIGHT_RULES_KEY = 'LIGHTRULES'
ALL_RULES_KEY = 'ALL'
ALL_SRCS_KEY = 'all_sources_key'
BUILD_FILE_NAME = 'BLD'
CC_BIN_TYPE = 'cc_bin'
CC_LIB_TYPE = 'cc_lib'
CC_PROTO_LIB_TYPE = 'cc_proto_lib'
CC_TEST_TYPE = 'cc_test'
CHANGE_CURR_DIR = 'chdir'
COMPILE_COMMAND_KEY = 'compile_command'
COMPILE_DEPS_KEY = 'compileDeps'
COMPILE_IGNORE_WARNINGS_KEY = 'ignore_compiler_warnings'
COMPILE_LIBS_KEY = 'compile_libs'
COMPILE_PARAMS_KEY = 'compile_params'
DEPS_KEY = 'deps'
DOWNLOAD_CHUNK_SIZE = 1024
EXTRACT_RESOURCES_DEP_KEY = 'extract_deps'
FILE_COLL_TYPE = 'file_coll'
FILE_PACKAGE_KEY = 'file_package'
HDRS_KEY = 'hdrs'
JAR_INCLUDE_KEY = 'jar_include_paths'
JAR_MANIFEST_PATH = os.path.join('.', 'META-INF')
JAR_EXCLUDE_KEY = 'jar_exclude_paths'
JAVA_BIN_TYPE = 'java_bin'
JAVA_FAKE_MAIN_CLASS = 'java_fake_main_class'
JAVA_LIB_TYPE = 'java_lib'
JAVA_LINK_JAR_COMMAND = 'java_link_jar'
JAVA_OUTER_CLASSNAME_KEY = 'java_outer_classname'
JAVA_PACKAGE_KEY = 'java_package'
JAVA_PROTO_LIB_TYPE = 'java_proto_lib'
JAVA_PROTO_LINK_LIBS_KEY = 'java_proto_link_libs'
JAVA_TEST_TYPE = 'java_test'
JAVA_TESTNG_GROUPS = 'test_groups'
JAVA_TESTNG_ROOT = 'org.testng.TestNG'
JAVA_VERSION_KEY = 'java_version'
JAVAC_OUTDIR_KEY = 'javac_outdir_key'
LINK_COMMANDS_KEY = 'link_commands'
LINK_INCLUDE_DEPS_KEY = 'includeDeps'
LINK_LIBS_KEY = 'link_libs'
MAIN_CLASS_KEY = 'main_class'
MAIN_METHOD_KEY = 'main_method'
MAVEN_ARTIFACT_ID_KEY = 'artifact_id'
MAVEN_CLASSIFIER_KEY = 'classifier'
MAVEN_GROUP_ID_KEY = 'group_id'
MAVEN_IDENTIFIERS_KEY = 'maven_id'
MAVEN_REPO_URL_KEY = 'repo_url'
MAVEN_SPECS_KEY = 'maven_specs'
MAVEN_VERSION_KEY = 'version'
NAME_KEY = 'rule_name'
OTHER_INCLUDE_DIRS = 'incdirs'
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
PERFORM_ZIP_ALL_CURRDIR = 'perform_zip_all_currdir'
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
PYTHON_SKIPLINT_KEY = 'py_skiplint'
PYTHON_TEST_TYPE = 'py_test'
RELEASE_PACKAGE_TYPE = 'release_package'
RELEASE_TEST_COMMANDS_KEY = 'release_test_commands'
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
TEST_CLASS_KEY = 'test_class'
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


class Error(Exception):
  """Generic error class."""


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


def cleandir(dir_path):
  """Clean and create directory."""
  assert ((dir_path.startswith(BUILD_OUT_DIR)) or
          (dir_path.startswith(BUILD_WORK_DIR)))
  if path_exists(dir_path):
    shutil.rmtree(dir_path)
  os.makedirs(dir_path)


def download_cached_item(url, file_path):
  """Download url to file path."""
  # Assuming all real cached items would be at least 5 bytes. This check for
  # file size is needed when accidentally zero length files have been
  # downloaded.
  if path_exists(file_path) and os.stat(file_path).st_size > 5:
    return
  subprocess.check_call(get_mkdir_command(os.path.dirname(file_path)))
  temp_path = file_path + '.temp'
  with open(temp_path, 'wb') as file_object:
    try:
      response = urllib2.urlopen(url)
    except urllib2.HTTPError as exc:
      raise Error('{} {} {}'.format(exc.code, exc.reason, url))
    while True:
      chunk = response.read(DOWNLOAD_CHUNK_SIZE)
      if not chunk:
        break
      file_object.write(chunk)
      file_object.flush()
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


def expand_env_vars(dep_path):
  """Retrieve dependency file path by expanding environment variables."""
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
      obj = dict([(k.encode('ascii'), _ascii_encoder(v))
                 for (k, v) in obj.iteritems()])
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


def _get_current_snapshot_text(file_list):
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
  return found_all, curr_snapshot_text


def needs_build(working_dir, file_list):
  """Checks file list snapshot for any changes."""
  tracer = logging.debug
  cache_file = os.path.join(working_dir, CACHE_FILE_NAME)
  if not path_exists(cache_file):
    tracer('Did not find cache file at %s', log_normalize(cache_file))
    return True
  found_all, curr_snapshot_text = _get_current_snapshot_text(file_list)
  if not found_all:
    tracer('Did not find all files present.')
    return True
  cached_text = read_file(cache_file)
  if curr_snapshot_text != cached_text:
    tracer('Snapshot mismatch.')
    tracer('\nCache file: \n%s', cached_text)
    tracer('\nCurrent snapshot: \n%s', curr_snapshot_text)
    return True
  return False


def save_file_list_cache(working_dir, file_list):
  """Saves file list snapshot to disk."""
  found_all, curr_snapshot_text = _get_current_snapshot_text(file_list)
  assert found_all
  cache_file = os.path.join(working_dir, CACHE_FILE_NAME)
  write_file(cache_file, curr_snapshot_text)


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
