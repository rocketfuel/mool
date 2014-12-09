"""Implement the rules of each Scala build utility type."""
import os

import java_common as jc
import shared_utils as su


class Error(Exception):
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
    # Hard coded for the time being to support ScalaTest.
    classpath = ["{}/*".format(rule_details[su.WDIR_CLSDEPS_KEY])]
    classpath.append(rule_details[su.OUT_KEY])
    version = rule_details.get(su.SCALA_VERSION_KEY, su.SCALA_DEFAULT_VERSION)
    test_command = [su.get_scala_runtime(version), '-cp', ':'.join(classpath),
                    'org.scalatest.run', rule_details[su.TEST_CLASS_KEY]]
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


class ScalaLibrary(ScalaCommon):
  """Handler class for Scala lib build rules."""


class ScalaBinary(ScalaCommon):
  """Handler class for Scala binary build rules."""


class ScalaTest(ScalaCommon):
  """Handler class for Scala test build rules."""
