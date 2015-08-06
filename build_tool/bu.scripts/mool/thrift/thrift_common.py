"""Common class for helping with thrift libs rules."""
import os
import mool.shared_utils as su

HEADERS_OUT_DIR_NAME = 'include'
THRIFT_FILE_TAIL = '.thrift'

# Note: In case of cc thrift libs, there can be false positives as this string
# can match a commented service, but we do an assert check with what thrift
# generates and report to the user appropriately.
THRIFT_SERVICE_PATTERN_STRING = r'^service ([A-Za-z]\w+)'
THRIFT_NAMESPACE_PATTERN_STRING = r'^namespace ([a-z]+) ([a-zA-Z0-9\.]+)'

# For generated code from original thrift file.
GEN_CODE_DIR = 'GEN_CODE_DIR'
# Original thrift source code is linked/copied here.
SRC_CODE_DIR = 'SRC_CODE_DIR'


def get_thrift_compile_command(rule_details, out_path):
  """Get the protoc command line for specified parameters."""
  assert 1 == len(rule_details[su.SRCS_KEY])
  if su.CC_THRIFT_LIB_TYPE == rule_details[su.TYPE_KEY]:
    gen_flags = 'cpp:include_prefix'
  elif su.JAVA_THRIFT_LIB_TYPE == rule_details[su.TYPE_KEY]:
    gen_flags = 'java:private-members:fullcamel'
  elif su.PYTHON_THRIFT_LIB_TYPE == rule_details[su.TYPE_KEY]:
    gen_flags = 'py:new_style:utf8strings'
  else:
    assert False
  src_file = su.get_relative_path(rule_details[su.POSSIBLE_PREFIXES_KEY],
                                  rule_details[su.SRCS_KEY][0])
  compile_command = su.THRIFT_COMPILER.split()
  compile_command.extend(['--gen', gen_flags, '-out', out_path, '-I', '.'])
  compile_command.append(src_file)
  return compile_command


class ThriftCommon(object):
  """Common functionality for building libraries from thrift."""

  @classmethod
  def _get_thrift_file_prefix(cls, rule_details):
    """Get thrift file name prefix."""
    thrift_file_name = os.path.basename(rule_details[su.SRCS_KEY][0])
    return thrift_file_name[:-len(THRIFT_FILE_TAIL)]

  @classmethod
  def _get_services_list(cls, rule_details):
    """Get list of services defined in thrift file."""
    thrift_file = rule_details[su.SRCS_KEY][0]
    services_list = su.grep_lines_in_file(
        thrift_file, THRIFT_SERVICE_PATTERN_STRING)
    services = [s[0] for _, s in services_list]
    return services

  @classmethod
  def _validate(cls, rule_details, _):
    """Validate rule specification."""
    assert 1 == len(rule_details[su.SRCS_KEY])
    assert rule_details[su.SRCS_KEY][0].endswith(THRIFT_FILE_TAIL)
    assert su.HDRS_KEY not in rule_details

  @classmethod
  def _get_work_dirs(cls, rule_details):
    """Returns list of must create work directories for code compilation."""
    return [rule_details[su.OUTDIR_KEY],
            rule_details[su.WDIR_KEY],
            rule_details[SRC_CODE_DIR],
            rule_details[GEN_CODE_DIR]]

  @classmethod
  def _get_gen_code_dir(cls, rule_details):
    """Helper functions to return directory path having generated code."""
    return rule_details[GEN_CODE_DIR]

  @classmethod
  def get_lang_namespace(cls, language, rule_details):
    """Returns namespace of given language."""
    thrift_file = rule_details[su.SRCS_KEY][0]
    namespaces = su.grep_lines_in_file(
        thrift_file, THRIFT_NAMESPACE_PATTERN_STRING)
    for _, details in namespaces:
      if details[0] == language:
        return details[1]
    assert False, "No namespace found with name {}".format(language)

  @classmethod
  def setup(cls, rule_details, details_map):
    """Common setup for compiling thrift code."""
    cls._validate(rule_details, details_map)
    su.set_workdir_child(rule_details, SRC_CODE_DIR, 'src')
    su.set_workdir_child(rule_details, GEN_CODE_DIR, 'generated')
