"""Rules for cc protocol buffers."""
import logging
import os
import mool.shared_utils as su

PROTO_FILE_TAIL = '.proto'
PROTO_GEN_CC_TAIL = '.pb.cc'
PROTO_GEN_HDR_TAIL = '.pb.h'


class CplusplusProto(object):
  """Proto library builder functions for C++."""
  @classmethod
  def _set_proto_name_info(cls, rule_details):
    """Set information from proto file name."""
    proto_file_name = os.path.basename(rule_details[su.SRCS_KEY][0])
    assert proto_file_name.endswith(PROTO_FILE_TAIL)
    proto_file_name = proto_file_name[:-len(PROTO_FILE_TAIL)]
    proto_name_header = os.path.join(
        rule_details[su.WDIR_KEY], rule_details[su.PATH_SUBDIR_KEY],
        proto_file_name)
    rule_details[su.OUT_HEADER_KEY] = proto_name_header + PROTO_GEN_HDR_TAIL
    rule_details[su.OUT_CC_KEY] = proto_name_header + PROTO_GEN_CC_TAIL
    rule_details[su.HDRS_KEY] = [
        os.path.join(rule_details[su.OUTDIR_KEY],
                     proto_file_name + PROTO_GEN_HDR_TAIL)]

  @classmethod
  def _validate(cls, rule_details, details_map):
    """Validate rule state."""
    assert 1 == len(rule_details[su.SRCS_KEY])
    assert rule_details[su.SRCS_KEY][0].endswith(PROTO_FILE_TAIL)
    for dep_rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      assert su.CC_PROTO_LIB_TYPE == details_map[dep_rule_symbol][su.TYPE_KEY]
    assert su.HDRS_KEY not in rule_details

  @classmethod
  def _set_all_srcs(cls, rule_details, details_map):
    """Set all sources."""
    all_srcs = []
    current_rule_symbol = rule_details[su.SYMBOL_KEY]
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      all_srcs.extend(details_map[rule_symbol][su.SRCS_KEY])
      if current_rule_symbol != rule_symbol:
        all_srcs.extend(details_map[rule_symbol][su.HDRS_KEY])
    rule_details[su.ALL_SRCS_KEY] = sorted(list(set(all_srcs)))

  @classmethod
  def _set_all_dep_paths(cls, rule_details):
    """Set all dependency paths."""
    all_dep_paths = rule_details[su.ALL_SRCS_KEY][:]
    all_dep_paths.append(rule_details[su.OUT_KEY])
    all_dep_paths.extend(rule_details[su.HDRS_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(all_dep_paths)
    rule_details[su.ALL_DEP_PATHS_KEY] = sorted(
        list(set(rule_details[su.ALL_DEP_PATHS_KEY])))

  @classmethod
  def _get_compile_command(cls, rule_details):
    """Get command to compile generated C++ code to a library."""
    compile_command = su.CC_COMPILER.split()
    compile_command.extend([
        '-isystem', '.', '-isystem', su.CC_PROTOBUF_INCDIR, '-c',
        su.get_relative_path(
            rule_details[su.POSSIBLE_PREFIXES_KEY],
            rule_details[su.OUT_CC_KEY]),
        '-o', rule_details[su.OUT_KEY]])
    return compile_command

  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup using details map."""
    cls._validate(rule_details, details_map)
    su.init_rule_common(
        rule_details, '{}.o'.format(rule_details[su.NAME_KEY]), [su.SRCS_KEY])
    cls._set_proto_name_info(rule_details)
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform(
        [su.BUILD_OUT_DIR, rule_details[su.WDIR_KEY]])
    cls._set_all_srcs(rule_details, details_map)
    cls._set_all_dep_paths(rule_details)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s, %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]),
                 su.log_normalize(rule_details[su.HDRS_KEY][0]))
    directory_list = [rule_details[su.OUTDIR_KEY], rule_details[su.WDIR_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.WDIR_KEY]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.append(su.get_proto_compile_command(rule_details, '.'))
    command_list.append(['cp', rule_details[su.OUT_HEADER_KEY],
                         rule_details[su.HDRS_KEY][0]])
    command_list.append(cls._get_compile_command(rule_details))
    return command_list
