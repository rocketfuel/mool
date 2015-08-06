"""Implement the rules of each Java build utility type."""
import json
import logging
import os
import subprocess

import mool.jar_merger as jm
import mool.shared_utils as su
import mool.jar_testng_runner as testng_runner


JAVA_VERSION_DEP_RULE_TYPES = [su.JAVA_BIN_TYPE, su.JAVA_LIB_TYPE,
                               su.JAVA_TEST_TYPE]
MAX_LOOP_COUNT = 5000


class Error(su.Error):
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


def get_maven_download_paths(maven_identifiers):
  """Returns tuple for jar download url and jar download paths in cache for
  main and sources jars."""
  artifact_id, classifier, group_id, repo_url, version = maven_identifiers
  group_id = group_id.replace('.', '/')
  jar_name = '{}-{}{}.jar'.format(artifact_id, version, classifier)
  src_jar_name = '{}-{}{}-sources.jar'.format(artifact_id, version, classifier)
  url = '/'.join([repo_url, group_id, artifact_id, version, jar_name])
  output_path = os.path.join(su.JAR_SEARCH_PATH, group_id, artifact_id,
                             version, jar_name)
  srcs_url = '/'.join([repo_url, group_id, artifact_id, version, src_jar_name])
  srcs_output_path = os.path.join(su.JAR_SEARCH_PATH, group_id, artifact_id,
                                  version, src_jar_name)
  return (url, output_path, srcs_url, srcs_output_path)


def export_mvn_deps(params):
  """Export mvn deps to file."""
  all_deps = []

  def _expand_deps(dep_list, dep_type):
    """Format the given dependency list into dictionary."""
    for dep in dep_list:
      artifact_id, classifier, group_id, repo_url, version, file_path = dep
      jar_url, jar_path, srcs_url, srcs_path = (
          get_maven_download_paths(dep[0:5]))
      dep_elem = {'artifactId': artifact_id, 'classifier': classifier,
                  'groupId': group_id, 'jarBuildPath': file_path,
                  'jarCachePath': jar_path, 'jarUrl': jar_url,
                  'repoUrl': repo_url, 'scope': dep_type,
                  'srcsCachePath': srcs_path, 'srcsUrl': srcs_url,
                  'version': version}
      all_deps.append(dep_elem)

  out_file, maven_included_deps, maven_compile_deps = params
  _expand_deps(maven_included_deps, 'compile')
  _expand_deps(maven_compile_deps, 'provided')
  all_deps = sorted(all_deps, key=lambda x: x['scope'])
  mvn_dict = {'deps': all_deps}
  su.write_file(out_file, json.dumps(mvn_dict, indent=4))


def java_testng_runner(args):
  """Run java tests using TestNg framework."""
  testng_runner.do_main(args)


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


def handle_java_version_key(rule_details, details_map):
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
    dep_rule = details_map[dependency]
    dep_java_ver = dep_rule.get(su.JAVA_VERSION_KEY, su.JAVA_DEFAULT_VERSION)
    if all([dep_rule[su.TYPE_KEY] in valid_rule_types,
            (any(dep_rule.get(su.SRCS_KEY, [])) or
             su.JAVA_VERSION_KEY in dep_rule),
            not compare_java_versions(java_version, dep_java_ver)]):
      msg = ('Java version dependency check failed.\n'
             'Build rule {}(Java {}) depends on {}(Java {})!')
      msg = msg.format(rule_details[su.SYMBOL_KEY], java_version,
                       dep_rule[su.SYMBOL_KEY], dep_java_ver)
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


def _get_recursive_compile_deps(rule_details, details_map):
  """Get all compile time deps dependencies for a rule."""
  final_deps = set()
  active_set = set(rule_details.get(su.DEPS_KEY))
  iters = 0
  while active_set:
    iters += 1
    assert iters <= MAX_LOOP_COUNT, "Too many recursive iterations."
    temp_set = set()
    for dep in active_set:
      final_deps = final_deps.union(
          set(details_map[dep].get(su.COMPILE_DEPS_KEY, [])))
      temp_set = temp_set.union(details_map[dep][su.DEPS_KEY])
    active_set = temp_set
  return final_deps


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
    url, output_path, srcs_url, srcs_output_path = (
        get_maven_download_paths(rule_details[su.MAVEN_IDENTIFIERS_KEY]))

    if su.MAVEN_PREFER_LOCAL_REPO:
      try:
        new_url = url.replace(
            rule_details[su.MAVEN_IDENTIFIERS_KEY][3],
            'file://{}'.format(su.MAVEN_PREFER_LOCAL_REPO))
        su.download_cached_item(new_url, output_path)
      except IOError:
        logging.warn('File not found in local repo!! Trying remote repo.')
        su.download_cached_item(url, output_path)
    else:
      su.download_cached_item(url, output_path)

    if su.is_developer_mode():
      try:
        su.download_cached_item(srcs_url, srcs_output_path)
      except IOError:
        pass
    return [output_path]

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
    compile_libs = [details_map[r][su.OUT_KEY]
                    for r in rule_details[su.COMPILE_DEPS_KEY]]
    # For java test rule, recursively add all the compile time dependencies
    # as run time dependencies of rule.
    if cls._is_test_rule(rule_details):
      all_compile_deps = _get_recursive_compile_deps(rule_details, details_map)
      compile_libs.extend(
          [details_map[dep][su.OUT_KEY] for dep in all_compile_deps])
    return link_libs, compile_libs, dep_sources

  @classmethod
  def _get_recursive_maven_deps(cls, rule_details, details_map):
    """Get all maven dependencies for a rule."""

    def _accumulate(deps_key, included_deps, compile_deps):
      """Accumulate maven dependencies from a dependency key."""
      for rule_symbol in rule_details[deps_key]:
        if rule_symbol == rule_details[su.SYMBOL_KEY]:
          continue
        dep_rule_details = details_map[rule_symbol]
        dep_maven_id = dep_rule_details.get(su.MAVEN_IDENTIFIERS_KEY, [])
        if dep_maven_id:
          included_deps.append(dep_maven_id + tuple([
              dep_rule_details[su.OUT_KEY]]))
        maven_deps_pair = dep_rule_details.get(su.MAVEN_DEPS_KEY, ([], []))
        included_deps.extend(maven_deps_pair[0])
        compile_deps.extend(maven_deps_pair[1])

    maven_included_deps = []
    maven_compile_deps = []
    _accumulate(su.DEPS_KEY, maven_included_deps, maven_compile_deps)
    _accumulate(su.COMPILE_DEPS_KEY, maven_compile_deps, maven_compile_deps)
    _accumulate(su.ALL_DEPS_KEY, maven_included_deps, maven_compile_deps)
    maven_included_deps = sorted(list(set(maven_included_deps)))
    maven_compile_deps = sorted(list(set(maven_compile_deps)))
    maven_compile_deps = [d for d in maven_compile_deps
                          if d not in maven_included_deps]
    return (maven_included_deps, maven_compile_deps)

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
    test_command = [su.JAVA_TESTNG_RUNNER, rule_details[su.OUT_KEY]]
    if su.TEST_CLASS_KEY in rule_details:
      test_command.append([rule_details[su.TEST_CLASS_KEY]])
    else:
      test_command.append(rule_details[su.TEST_CLASSES_KEY])
    for test_class in test_command[-1]:
      if test_class.endswith('.java'):
        raise Error(('Invalid test class name %s! It shouldn\'t end with '
                     '.java!') % test_class)
    working_dir = os.path.join(rule_details[su.WDIR_KEY], '.test.wdir')
    test_command.append(working_dir)
    test_command.append(rule_details.get(su.JAVA_TESTNG_GROUPS, ['unit']))
    test_command.append(rule_details[su.WDIR_CLSDEPS_KEY])
    test_command.append(rule_details.get(su.RUNTIME_PARAMS_KEY, []))
    ext_jar_files = [details_map[rule][su.OUT_KEY] for rule in rule_details[
                     su.EXTRACT_RESOURCES_DEP_KEY]]
    test_command.append(ext_jar_files)
    rule_details[su.TEST_COMMANDS_KEY] = [test_command]

  @classmethod
  def set_precompile_commands(cls, rule_details):
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
  def _check_dependency_versions(cls, rule_details, details_map):
    """Run all possible version checks across the dependencies."""
    handle_java_version_key(rule_details, details_map)

  @classmethod
  def setup(cls, rule_details, details_map):
    """Initializing build rule dictionary."""
    cls._check_dependency_versions(rule_details, details_map)
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
    rule_details[su.MAVEN_DEPS_KEY] = cls._get_recursive_maven_deps(
        rule_details, details_map)
    rule_details[su.EXPORTED_MVN_DEPS_FILE_KEY] = os.path.join(
        rule_details[su.OUTDIR_KEY], out_file + '.mvn_deps.json')
    link_libs, compile_libs, dep_sources = cls._get_all_deps(
        rule_details, details_map)
    rule_details[su.LINK_LIBS_KEY] = link_libs
    rule_details[su.COMPILE_LIBS_KEY] = link_libs[:]
    rule_details[su.COMPILE_LIBS_KEY].extend(compile_libs)
    cls.set_precompile_commands(rule_details)
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
    command_list.append([su.EXPORT_MVN_DEPS,
                         rule_details[su.EXPORTED_MVN_DEPS_FILE_KEY],
                         rule_details[su.MAVEN_DEPS_KEY][0],
                         rule_details[su.MAVEN_DEPS_KEY][1]])
    return command_list


class JavaLibrary(JavaCommon):
  """Handler class for Java lib build rules."""


class JavaBinary(JavaCommon):
  """Handler class for Java binary build rules."""


class JavaTest(JavaCommon):
  """Handler class for Java test build rules."""
