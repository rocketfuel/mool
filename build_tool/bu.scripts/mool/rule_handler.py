"""Rule handler module."""
import os

import mool.shared_utils as su
import mool.cc_proto as ccp
import mool.cc_common as ccc
import mool.file_collection as fc
import mool.java_common as jc
import mool.java_proto as jp
import mool.python_common as pc
import mool.python_proto as pp
import mool.release_package as rp
import mool.scala_common as sc


class Error(su.Error):
  """The error class for this module."""


class RuleHandler(object):
  """Shim layer across all rule handlers."""
  def __init__(self):
    """Initialize."""
    self._lookup = {
        su.CC_BIN_TYPE: ccc.CplusplusBinary(),
        su.CC_LIB_TYPE: ccc.CplusplusLibrary(),
        su.CC_PROTO_LIB_TYPE: ccp.CplusplusProto(),
        su.CC_TEST_TYPE: ccc.CplusplusTest(),
        su.FILE_COLL_TYPE: fc.FileCollection(),
        su.JAVA_BIN_TYPE: jc.JavaBinary(),
        su.JAVA_LIB_TYPE: jc.JavaLibrary(),
        su.JAVA_PROTO_LIB_TYPE: jp.JavaProtoLibrary(),
        su.JAVA_TEST_TYPE: jc.JavaTest(),
        su.PYTHON_BIN_TYPE: pc.PyBinary(),
        su.PYTHON_LIB_TYPE: pc.PyLibrary(),
        su.PYTHON_PROTO_LIB_TYPE: pp.PyProtoLibrary(),
        su.PYTHON_TEST_TYPE: pc.PyPyTest(),
        su.RELEASE_PACKAGE_TYPE: rp.ReleasePackage(),
        su.SCALA_BIN_TYPE: sc.ScalaBinary(),
        su.SCALA_LIB_TYPE: sc.ScalaLibrary(),
        su.SCALA_TEST_TYPE: sc.ScalaTest()}
    self._lookup_menu_message = 'Valid choices are: {}'.format(
        ', '.join([k for k in sorted(self._lookup)]))

  def rule_setup(self, rule_details, details_map):
    """Full setup using details map."""
    if rule_details[su.TYPE_KEY] not in self._lookup:
      raise Error('Unexpected rule type "{}" in {}\n{}'.format(
          rule_details[su.TYPE_KEY], rule_details[su.RULE_FILE_PATH],
          self._lookup_menu_message))
    # Maintain code sanity by enforcing path separation characters is not
    # present in source files.
    for src_file in rule_details.get(su.SRCS_KEY, []):
      if os.path.sep in src_file:
        raise Error('Unexpected separator in source file for: {}'.format(
            rule_details[su.RULE_FILE_PATH]))
    self._lookup[rule_details[su.TYPE_KEY]].setup(rule_details, details_map)

  def rule_build_commands(self, rule_details):
    """Generate build command line."""
    for src_file in rule_details.get(su.SRCS_KEY, []):
      if not su.path_exists(src_file):
        raise Error('File does not exist: {}'.format(src_file))
      if not su.path_isfile(src_file):
        raise Error('Souce file is not a file: {}'.format(src_file))
    return self._lookup[rule_details[su.TYPE_KEY]].build_commands(rule_details)

  def rule_include_deps_recursively(self, rule_details):
    """Check if dependency tree needs to be pruned at this node. This can be
       useful for performance reasons.
    """
    rule_module = self._lookup[rule_details[su.TYPE_KEY]]
    if hasattr(rule_module, 'include_deps_recursively'):
      return rule_module.include_deps_recursively(rule_details)
    return True

  @classmethod
  def rule_file_list(cls, rule_details):
    """Return a list of input and output files of this rule."""
    return list(set(rule_details[su.ALL_DEP_PATHS_KEY]))

  @classmethod
  def rule_test(cls, rule_details):
    """Generate test command line."""
    return rule_details.get(su.TEST_COMMANDS_KEY, [])
