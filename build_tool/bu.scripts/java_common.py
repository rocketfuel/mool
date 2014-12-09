"""Implement the rules of each Java build utility type."""
import logging
import os
import subprocess

import jar_merger as jm
import shared_utils as su


JAVA_VERSION_DEP_RULE_TYPES = [su.JAVA_BIN_TYPE, su.JAVA_LIB_TYPE,
                               su.JAVA_TEST_TYPE]


class Error(Exception):
  """Error class for this module."""


def perform_linking(link_details):
  """Perform Java linking of multiple jars to a single jar."""
  lib_details, jar_out_file, main_class = link_details
  jm.do_merge(lib_details, jar_out_file, main_class)


def perform_java_linkall_currdir(params):
  """Perform Java linking of current directory to single jar."""
  assert 1 == len(params)
  target_file = params[0]
  # Ensure current directory is not empty.
  subprocess.check_call(su.get_mkdir_command(su.JAR_MANIFEST_PATH))
  jar_create_command = [su.JAR_BIN, 'cf', target_file]
  jar_create_command.extend(os.listdir('.'))
  subprocess.check_call(jar_create_command)


def get_java_compile_command(rule_details, compile_libs, dir_path, file_list,
                             warn_as_error):
  """Get java compile command."""
  compile_params = rule_details.get(su.COMPILE_PARAMS_KEY, [])
  java_version = rule_details.get(su.JAVA_VERSION_KEY, su.JAVA_DEFAULT_VERSION)
  compile_command = su.get_javac_bin(java_version).split()
  if warn_as_error:
    compile_command.extend(['-Werror'])
  else:
    compile_command.extend(['-nowarn'])
  class_path = []
  if compile_libs:
    class_path.extend([c for c in compile_libs if isinstance(c, str)])
  class_path = ':'.join(class_path)
  if class_path:
    compile_command.extend(['-cp', class_path])
  compile_command.extend(['-d', dir_path])
  compile_command.extend(compile_params or [])
  compile_command.extend(file_list)
  return compile_command


def compare_java_versions(rule_version, dependency_version):
  """Compares two given java versions. rule_version should be greater than
  equal the dependency_version."""
  return float(rule_version) >= float(dependency_version)


def _handle_java_version_key(rule_details, details_map):
  """Set java compiler version and check the version dependencies on other
  rules. Any dependency of this rule shouldn't have a higher java version."""
  valid_rule_types = JAVA_VERSION_DEP_RULE_TYPES
  if all([su.JAVA_VERSION_KEY in rule_details,
          rule_details[su.TYPE_KEY] not in valid_rule_types]):
    raise Error(('Java version should only be specified for [{}]'
                 'types!').format(', '.join(valid_rule_types)))

  rule_dependencies = []
  rule_dependencies.extend(rule_details[su.DEPS_KEY])
  rule_dependencies.extend(rule_details[su.COMPILE_DEPS_KEY])
  java_version = rule_details.get(su.JAVA_VERSION_KEY, su.JAVA_DEFAULT_VERSION)
  for dependency in rule_dependencies:
    dep_java_ver = details_map[dependency].get(su.JAVA_VERSION_KEY,
                                               su.JAVA_DEFAULT_VERSION)
    if all([details_map[dependency][su.TYPE_KEY] in valid_rule_types,
            not compare_java_versions(java_version, dep_java_ver)]):
      msg = ('Java version dependency check failed.\n'
             'Build rule {}(Java {}) depends on {}(Java {})!')
      msg = msg.format(rule_details[su.SYMBOL_KEY], java_version,
                       details_map[dependency][su.SYMBOL_KEY], dep_java_ver)
      raise Error(msg)


def _get_maven_identifiers(maven_details):
  """Parse the maven details to obtain key identifiers."""
  artifact_id = maven_details[su.MAVEN_ARTIFACT_ID_KEY]
  classifier = maven_details.get(su.MAVEN_CLASSIFIER_KEY, '')
  classifier = '-{}'.format(classifier) if classifier else ''
  group_id = maven_details[su.MAVEN_GROUP_ID_KEY]
  repo_url = maven_details[su.MAVEN_REPO_URL_KEY]
  version = maven_details[su.MAVEN_VERSION_KEY]
  return artifact_id, classifier, group_id, repo_url, version


class JavaCommon(object):
  """Common Java handler functions."""
  @classmethod
  def _get_all_pc_deps(cls, rule_details):
    """Get precompiled deps of current rule."""
    pc_deps = rule_details.get(su.PC_DEPS_KEY, [])
    pc_deps = [su.expand_env_vars(f) for f in list(set(pc_deps))]
    if su.JAVA_TEST_TYPE == rule_details[su.TYPE_KEY]:
      pc_deps.extend(su.JAVA_TEST_DEFAULT_JARS)
    return pc_deps

  @classmethod
  def _is_test_rule(cls, rule_details):
    """Just check if the given rule is a test rule."""
    return rule_details[su.TYPE_KEY] == su.JAVA_TEST_TYPE

  @classmethod
  def _set_maven_identifiers(cls, rule_details):
    """Set maven identifiers of rule."""
    maven_identifiers = []
    maven_details = rule_details.get(su.MAVEN_SPECS_KEY, {})
    if maven_details:
      maven_identifiers = _get_maven_identifiers(maven_details)
    rule_details[su.MAVEN_IDENTIFIERS_KEY] = maven_identifiers

  @classmethod
  def _get_maven_dep(cls, rule_details):
    """Get maven dependency of rule."""
    if not rule_details[su.MAVEN_IDENTIFIERS_KEY]:
      return []
    assert not rule_details[su.SRCS_KEY]
    assert not rule_details[su.DEPS_KEY]
    assert rule_details[su.LINK_INCLUDE_DEPS_KEY]
    artifact_id, classifier, group_id, repo_url, version = (
        rule_details[su.MAVEN_IDENTIFIERS_KEY])
    group_id = group_id.replace('.', '/')
    jar_name = '{}-{}{}.jar'.format(artifact_id, version, classifier)
    srcs_jar_name = '{}-{}{}-sources.jar'.format(
        artifact_id, version, classifier)
    url = '{}/{}/{}/{}/{}'.format(repo_url, group_id, artifact_id, version,
                                  jar_name)
    output_path = os.path.join(su.JAR_SEARCH_PATH, group_id, artifact_id,
                               version, jar_name)
    srcs_url = '{}/{}/{}/{}/{}'.format(repo_url, group_id, artifact_id, version,
                                       srcs_jar_name)
    srcs_output_path = os.path.join(su.JAR_SEARCH_PATH, group_id, artifact_id,
                                    version, srcs_jar_name)
    su.download_cached_item(url, output_path)
    if su.is_developer_mode():
      try:
        su.download_cached_item(srcs_url, srcs_output_path)
      except su.Error:
        pass
    return [output_path]

  @classmethod
  def _get_compile_dep_utils(cls, rule_details, details_map, property_name):
    """Get list of specified property from all compile deps."""
    result = []
    for rule_symbol in rule_details[su.COMPILE_DEPS_KEY]:
      candidate = details_map[rule_symbol].get(property_name, None)
      if candidate:
        result.append(candidate)
    return result

  @classmethod
  def _get_all_deps(cls, rule_details, details_map):
    """Get all link libraries for a Java build rule."""
    link_libs = []
    dep_sources = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      if rule_symbol == rule_details[su.SYMBOL_KEY]:
        continue
      dep_rule_details = details_map[rule_symbol]
      if dep_rule_details[su.TYPE_KEY] == su.JAVA_PROTO_LIB_TYPE:
        link_libs.append(su.JAVA_PROTOBUF_JAR)
      link_libs.append(dep_rule_details[su.OUT_KEY])
      dep_sources.extend(dep_rule_details[su.SRCS_KEY])

    link_libs.extend(cls._get_all_pc_deps(rule_details))
    link_libs.extend(cls._get_maven_dep(rule_details))
    assert all([l.endswith('.jar') for l in link_libs])
    link_libs = sorted(list(set(link_libs)))
    compile_libs = cls._get_compile_dep_utils(
        rule_details, details_map, su.OUT_KEY)
    return link_libs, compile_libs, dep_sources

  @classmethod
  def _set_compile_command(cls, rule_details):
    """Set Java compile command."""
    rule_details[su.COMPILE_COMMAND_KEY] = []
    if not rule_details[su.SRCS_KEY]:
      return
    compile_libs = []
    if rule_details[su.COMPILE_LIBS_KEY]:
      compile_libs = [os.path.join(rule_details[su.WDIR_CLSDEPS_KEY], '*')]
    compile_command = get_java_compile_command(
        rule_details, compile_libs, rule_details[su.WDIR_TARGET_KEY],
        [su.get_relative_path(rule_details[su.POSSIBLE_PREFIXES_KEY], f)
         for f in rule_details[su.SRCS_KEY]],
        not rule_details[su.COMPILE_IGNORE_WARNINGS_KEY])
    rule_details[su.COMPILE_COMMAND_KEY].append(compile_command)

  @classmethod
  def _set_link_command(cls, rule_details):
    """Set Java link command."""
    main_class = rule_details.get(su.MAIN_CLASS_KEY,
                                  su.JAVA_FAKE_MAIN_CLASS)
    link_commands = []
    final_libs = []
    # Link classes from current rule to a jar.
    if rule_details[su.COMPILE_COMMAND_KEY]:
      link_commands.append(
          [su.CHANGE_CURR_DIR, rule_details[su.WDIR_TARGET_KEY]])
      link_commands.append([su.PERFORM_JAVA_LINK_ALL_CURRDIR,
                            rule_details[su.TEMP_OUT_KEY]])
      final_libs.append(rule_details[su.TEMP_OUT_KEY])
    # Pull in the dependencies that need to be included.
    if ((rule_details[su.LINK_LIBS_KEY] and
         rule_details[su.LINK_INCLUDE_DEPS_KEY])):
      final_libs.extend(rule_details[su.LINK_LIBS_KEY])
    # There must be some dependencies or sources. Otherwise the target would be
    # empty.
    assert final_libs
    link_commands.append(
        [su.JAVA_LINK_JAR_COMMAND,
         (rule_details.get(su.JAR_INCLUDE_KEY, []),
          rule_details.get(su.JAR_EXCLUDE_KEY, []), final_libs),
         rule_details[su.OUT_KEY], main_class])
    rule_details[su.LINK_COMMANDS_KEY] = link_commands

  @classmethod
  def _set_test_commands(cls, rule_details, details_map):
    """Initializing build rule dictionary."""
    working_dir = os.path.join(rule_details[su.WDIR_KEY], '.test.wdir')
    testng_groups = rule_details.get(su.JAVA_TESTNG_GROUPS, ['unit'])
    runtime_params = ','.join(
        rule_details.get(su.RUNTIME_PARAMS_KEY, []))
    test_command = [su.JAR_TESTER_SCRIPT, '-j', rule_details[su.OUT_KEY], '-w',
                    working_dir, '-cpd', rule_details[su.WDIR_CLSDEPS_KEY],
                    '-tc', rule_details[su.TEST_CLASS_KEY]]
    if runtime_params:
      test_command.extend(['-jp', '\'{}\''.format(runtime_params)])
    test_command.extend(['-g'] + testng_groups)
    if rule_details.get(su.EXTRACT_RESOURCES_DEP_KEY, None):
      jar_files = [details_map[rule][su.OUT_KEY] for rule in rule_details[
                   su.EXTRACT_RESOURCES_DEP_KEY]]
      test_command.extend(['-x'] + jar_files)
    rule_details[su.TEST_COMMANDS_KEY] = [test_command]

  @classmethod
  def _set_precompile_commands(cls, rule_details):
    """Set precompile link command for dependencies."""
    rule_details[su.PRECOMPILE_COMMANDS_KEY] = []
    if not rule_details[su.SRCS_KEY]:
      return
    # File-linking all compile-time dependencies to a single directory for the
    # benefit of javac compiler. The actual file names here are not important,
    # so we use an increasing sequence of names. Also, note that at this level
    # it is possible to have different jars in the clsdeps directory with
    # different implementations of the same class. The merge-conflict however
    # would be resolved at final link time. This is a performance optimization
    # used for faster coding.
    compile_libs = rule_details[su.COMPILE_LIBS_KEY]
    for index in xrange(len(compile_libs)):
      compile_lib = compile_libs[index]
      dst_file = os.path.join(rule_details[su.WDIR_CLSDEPS_KEY],
                              'f{}.jar'.format(index))
      file_link_command = su.get_copy_command(compile_lib, dst_file, True)
      rule_details[su.PRECOMPILE_COMMANDS_KEY].append(file_link_command)

  @classmethod
  def _set_all_dep_paths(cls, rule_details, link_libs, dep_sources):
    """Set all dependency paths list for the rule."""
    all_dep_paths = rule_details[su.SRCS_KEY][:]
    all_dep_paths.extend(link_libs)
    all_dep_paths.extend(dep_sources)
    all_dep_paths.append(rule_details[su.OUT_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(sorted(list(set(all_dep_paths))))

  @classmethod
  def _normalize_fields(cls, rule_details):
    """Normalize fields in rule details."""
    if su.RULE_NORMALIZED_KEY in rule_details:
      return
    rule_details[su.COMPILE_DEPS_KEY] = (
        rule_details.get(su.COMPILE_DEPS_KEY, []))
    rule_details[su.COMPILE_PARAMS_KEY] = (
        rule_details.get(su.COMPILE_PARAMS_KEY, []))
    if cls._is_test_rule(rule_details):
      # Unit tests should be fast to build and execute, otherwise valuable
      # developer time would end up being misused. If an
      # all-dependency-included test jar is really needed, includeDeps should
      # be set to "True" explicitly in a copy of the rule in the BLD file. This
      # all inclusive rule can be packaged separately.
      rule_details[su.LINK_INCLUDE_DEPS_KEY] = su.string_to_bool(
          rule_details.get(su.LINK_INCLUDE_DEPS_KEY, 'False'))
    else:
      rule_details[su.LINK_INCLUDE_DEPS_KEY] = su.string_to_bool(
          rule_details.get(su.LINK_INCLUDE_DEPS_KEY, 'True'))
    # Do a sanity check. A build rule with zero source files must include
    # dependencies. Otherwise, the only point served is to make BLD files more
    # compact. Why not achieve build efficiency as well?
    if not rule_details.get(su.SRCS_KEY, []):
      assert rule_details[su.LINK_INCLUDE_DEPS_KEY]
    rule_details[su.COMPILE_IGNORE_WARNINGS_KEY] = su.string_to_bool(
        rule_details.get(su.COMPILE_IGNORE_WARNINGS_KEY, 'False'))
    rule_details[su.RULE_NORMALIZED_KEY] = True

  @classmethod
  def setup(cls, rule_details, details_map):
    """Initializing build rule dictionary."""
    _handle_java_version_key(rule_details, details_map)
    out_file = '{}.jar'.format(rule_details[su.NAME_KEY])
    su.init_rule_common(rule_details, out_file, [su.SRCS_KEY])
    su.set_workdir_child(rule_details, su.WDIR_CLSDEPS_KEY, 'clsdeps')
    su.set_workdir_child(rule_details, su.WDIR_SRC_KEY, 'code')
    su.set_workdir_child(rule_details, su.WDIR_TARGET_KEY, 'target')
    su.set_workdir_child(rule_details, su.TEMP_OUT_KEY, '.temp.' + out_file)
    cls._normalize_fields(rule_details)
    if cls._is_test_rule(rule_details):
      cls._set_test_commands(rule_details, details_map)
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    cls._set_maven_identifiers(rule_details)
    link_libs, compile_libs, dep_sources = cls._get_all_deps(
        rule_details, details_map)
    rule_details[su.LINK_LIBS_KEY] = link_libs
    rule_details[su.COMPILE_LIBS_KEY] = link_libs[:]
    rule_details[su.COMPILE_LIBS_KEY].extend(compile_libs)
    cls._set_precompile_commands(rule_details)
    rule_details[su.ALL_SRCS_KEY] = rule_details[su.SRCS_KEY][:]
    cls._set_all_dep_paths(rule_details, link_libs, dep_sources)
    cls._set_compile_command(rule_details)
    cls._set_link_command(rule_details)

  @classmethod
  def include_deps_recursively(cls, rule_details):
    """Dependency graph pruning optimization."""
    cls._normalize_fields(rule_details)
    if rule_details[su.TYPE_KEY] != su.JAVA_LIB_TYPE:
      return True
    if rule_details[su.LINK_INCLUDE_DEPS_KEY]:
      # If the jar built by a java library includes all its dependencies,
      # there is no point in including these dependencies in the all_deps key.
      return False
    return True

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY],
                      rule_details[su.WDIR_CLSDEPS_KEY],
                      rule_details[su.WDIR_SRC_KEY],
                      rule_details[su.WDIR_TARGET_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.WDIR_SRC_KEY]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.extend(rule_details[su.PRECOMPILE_COMMANDS_KEY])
    command_list.extend(rule_details[su.COMPILE_COMMAND_KEY])
    command_list.extend(rule_details[su.LINK_COMMANDS_KEY])
    return command_list


class JavaLibrary(JavaCommon):
  """Handler class for Java lib build rules."""


class JavaBinary(JavaCommon):
  """Handler class for Java binary build rules."""


class JavaTest(JavaCommon):
  """Handler class for Java test build rules."""
