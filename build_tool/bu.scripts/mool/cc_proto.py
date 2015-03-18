"""Rules for cc protocol buffers."""
import logging
import os
import mool.shared_utils as su


PROTO_FILE_TAIL = '.proto'


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
    rule_details[su.OUT_HEADER_KEY] = proto_name_header + '.pb.h'
    rule_details[su.OUT_CC_KEY] = proto_name_header + '.pb.cc'

  @classmethod
  def _set_all_srcs(cls, rule_details, details_map):
    """Set all sources list for downstream consumption."""
    all_srcs = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      assert su.CC_PROTO_LIB_TYPE == other_rule_details[su.TYPE_KEY]
      all_srcs.append(other_rule_details[su.SRCS_KEY][0])
    all_srcs.append(rule_details[su.SRCS_KEY][0])
    rule_details[su.ALL_SRCS_KEY] = all_srcs

  @classmethod
  def _set_all_dep_paths(cls, rule_details):
    """Set all dependency paths."""
    all_dep_paths = rule_details[su.ALL_SRCS_KEY][:]
    all_dep_paths.extend(
        [rule_details[su.OUT_HEADER_KEY], rule_details[su.OUT_CC_KEY]])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(list(set(all_dep_paths)))

  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup using details map."""
    assert 1 == len(rule_details[su.SRCS_KEY])
    su.init_rule_common(rule_details, None, [su.SRCS_KEY])
    cls._set_proto_name_info(rule_details)
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    cls._set_all_srcs(rule_details, details_map)
    rule_details[su.HDRS_KEY] = [rule_details[su.OUT_HEADER_KEY]]
    cls._set_all_dep_paths(rule_details)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s, %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_CC_KEY]),
                 su.log_normalize(rule_details[su.OUT_HEADER_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY], rule_details[su.WDIR_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.WDIR_KEY]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.append(su.get_proto_compile_command(rule_details, '.'))
    return command_list
