"""Rules for Python protocol buffers."""
import logging
import os
import mool.shared_utils as su


class PyProtoLibrary(object):
  """Proto library builder functions for Python.

  From the README:
    The Python implementation of Protocol Buffers is not as mature as the C++
    and Java implementations.  It may be more buggy, and it is known to be
    pretty slow at this time.

  The main motivation of building this integration was to implement file
  collection rules.
  """
  @classmethod
  def _set_all_srcs(cls, rule_details, details_map):
    """Set all sources list for downstream consumption."""
    all_srcs = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      assert su.PYTHON_PROTO_LIB_TYPE == other_rule_details[su.TYPE_KEY]
      all_srcs.append(other_rule_details[su.SRCS_KEY][0])
    rule_details[su.ALL_SRCS_KEY] = all_srcs

  @classmethod
  def _set_all_dep_paths(cls, rule_details):
    """Set all dependency paths."""
    all_dep_paths = rule_details[su.ALL_SRCS_KEY][:]
    all_dep_paths.append(rule_details[su.OUT_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(list(set(all_dep_paths)))

  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup using details map."""
    assert 1 == len(rule_details[su.SRCS_KEY])
    su.init_rule_common(rule_details, rule_details[su.NAME_KEY], [su.SRCS_KEY])
    su.set_workdir_child(rule_details, su.PROTO_SRCS_KEY, 'proto_src')
    su.set_workdir_child(rule_details, su.PROTO_OUTDIR_KEY, 'proto_outfiles')
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    cls._set_all_srcs(rule_details, details_map)
    cls._set_all_dep_paths(rule_details)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY], rule_details[su.WDIR_KEY],
                      rule_details[su.PROTO_OUTDIR_KEY],
                      rule_details[su.PROTO_SRCS_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.PROTO_SRCS_KEY]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.append(
        su.get_proto_compile_command(rule_details,
                                     rule_details[su.PROTO_OUTDIR_KEY]))
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.PROTO_OUTDIR_KEY]])
    command_list.append([su.PYTHON_CREATE_INITIALIZERS])
    for pc_dep in rule_details.get(su.PC_DEPS_KEY, []):
      pc_dep = su.expand_env_vars(pc_dep)
      command_list.append([su.PYTHON_EXPAND_LIB, pc_dep, False])
    tmp_out_file = os.path.join(rule_details[su.PROTO_SRCS_KEY],
                                '.tmp.' + rule_details[su.NAME_KEY])
    command_list.append(
        [su.PYTHON_LINK_ALL, su.PYTHON_LIB_TYPE,
         su.PYTHON_FAKE_MAIN_METHOD, tmp_out_file, rule_details[su.OUT_KEY]])
    return command_list
