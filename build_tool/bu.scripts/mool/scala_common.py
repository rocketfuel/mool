"""Implement the rules of each Scala build utility type."""
import os

import mool.java_common as jc
import mool.shared_utils as su


SCALA_VERSION_DEP_RULE_TYPES = [su.SCALA_BIN_TYPE, su.SCALA_LIB_TYPE,
                                su.SCALA_TEST_TYPE]


class Error(su.Error):
  """Error class for this module."""


def get_scala_compile_command(rule_details, compile_libs, dir_path, file_list,
                              warn_as_error):
  """Get scala compile command."""
  compile_params = rule_details.get(su.COMPILE_PARAMS_KEY, [])
  version = rule_details.get(su.SCALA_VERSION_KEY, su.SCALA_DEFAULT_VERSION)
  compile_command = [su.get_scala_compiler(version)]
  if warn_as_error:
    compile_command.append('-Xfatal-warnings')
  else:
    compile_command.append('-nowarn')
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


def _compare_scala_versions(version, dep_version):
  """We restrict the dependencies to same major versions."""
  return version == dep_version


def _check_scala_dependencies(rule_details, details_map):
  """Enforce scala version dependency checks."""
  # Unlike Java, scala binaries are not backward compatible across major
  # versions. Since we have multiple major versions, make sure that all
  # dependencies of a rule are of same version.
  valid_rule_types = SCALA_VERSION_DEP_RULE_TYPES
  if all([su.SCALA_VERSION_KEY in rule_details,
          rule_details[su.TYPE_KEY] not in valid_rule_types]):
    raise Error(('Scala version should only be specified for [{}]'
                 'types!').format(', '.join(valid_rule_types)))

  rule_dependencies = []
  rule_dependencies.extend(rule_details[su.DEPS_KEY])
  rule_dependencies.extend(rule_details[su.COMPILE_DEPS_KEY])
  version = rule_details.get(su.SCALA_VERSION_KEY, su.SCALA_DEFAULT_VERSION)
  for dependency in rule_dependencies:
    dep_rule = details_map[dependency]
    dep_version = dep_rule.get(su.SCALA_VERSION_KEY, su.SCALA_DEFAULT_VERSION)
    if all([dep_rule[su.TYPE_KEY] in valid_rule_types,
            (any(dep_rule.get(su.SRCS_KEY, [])) or
             su.SCALA_VERSION_KEY in dep_rule),
            not _compare_scala_versions(version, dep_version)]):
      msg = ('Scala version dependency check *across major versions* failed.\n'
             'Build rule {}(Scala {}) depends on {}(Scala {})!')
      msg = msg.format(rule_details[su.SYMBOL_KEY], version,
                       dep_rule[su.SYMBOL_KEY], dep_version)
      raise Error(msg)


class ScalaCommon(jc.JavaCommon):
  """Common Scala handler functions."""
  @classmethod
  def _get_all_pc_deps(cls, rule_details):
    """Get precompiled deps of current rule."""
    pc_deps = rule_details.get(su.PC_DEPS_KEY, [])
    pc_deps = [su.expand_env_vars(f) for f in list(set(pc_deps))]
    return pc_deps

  @classmethod
  def _is_test_rule(cls, rule_details):
    """Just check if the given rule is a test rule."""
    return rule_details[su.TYPE_KEY] == su.SCALA_TEST_TYPE

  @classmethod
  def _set_compile_command(cls, rule_details):
    """Set Java compile command."""
    rule_details[su.COMPILE_COMMAND_KEY] = []
    if not rule_details[su.SRCS_KEY]:
      return
    compile_libs = []
    if rule_details[su.COMPILE_LIBS_KEY]:
      compile_libs = [os.path.join(rule_details[su.WDIR_CLSDEPS_KEY], '*')]
    compile_command = get_scala_compile_command(
        rule_details, compile_libs, rule_details[su.WDIR_TARGET_KEY],
        [su.get_relative_path(rule_details[su.POSSIBLE_PREFIXES_KEY], f)
         for f in rule_details[su.SRCS_KEY]],
        not rule_details[su.COMPILE_IGNORE_WARNINGS_KEY])
    rule_details[su.COMPILE_COMMAND_KEY].append(compile_command)

  @classmethod
  def _set_test_commands(cls, rule_details, details_map):
    """Initializing build rule dictionary."""
    # TODO: Hard coded for the time to support ScalaTest. Allow support for
    # other testing frameworks.
    classpath = ["{}/*".format(rule_details[su.WDIR_CLSDEPS_KEY])]
    classpath.append(rule_details[su.OUT_KEY])
    version = rule_details.get(su.SCALA_VERSION_KEY, su.SCALA_DEFAULT_VERSION)
    test_command = [su.get_scala_runtime(version), '-cp', ':'.join(classpath),
                    'org.scalatest.run']
    if su.TEST_CLASS_KEY in rule_details:
      test_command.append(rule_details[su.TEST_CLASS_KEY])
    else:
      test_command.extend(rule_details[su.TEST_CLASSES_KEY])
    rule_details[su.TEST_COMMANDS_KEY] = [test_command]

  @classmethod
  def include_deps_recursively(cls, rule_details):
    """Dependency graph pruning optimization."""
    cls._normalize_fields(rule_details)
    if rule_details[su.TYPE_KEY] != su.SCALA_LIB_TYPE:
      return True
    if rule_details[su.LINK_INCLUDE_DEPS_KEY]:
      # If the jar built by a java library includes all its dependencies,
      # there is no point in including these dependencies in the all_deps key.
      return False
    return True

  @classmethod
  def _check_dependency_versions(cls, rule_details, details_map):
    """Run all possible version checks across the dependencies."""
    jc.handle_java_version_key(rule_details, details_map)
    _check_scala_dependencies(rule_details, details_map)


# TODO: Refactor JavaCommon and ScalaCommon code to make maximum code reuse.
class ScalaLibrary(ScalaCommon):
  """Handler class for Scala lib build rules."""


class ScalaBinary(ScalaCommon):
  """Handler class for Scala binary build rules."""


class ScalaTest(ScalaCommon):
  """Handler class for Scala test build rules."""
