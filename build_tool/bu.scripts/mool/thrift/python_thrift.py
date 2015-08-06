"""Rules for building Python thrift library."""
import logging
import os
import mool.shared_utils as su
import mool.thrift.thrift_common as tc


class PyThriftLibrary(tc.ThriftCommon):
  """Thrift library builder module for Python."""
  @classmethod
  def _set_all_srcs(cls, rule_details, details_map):
    """Set all sources list for downstream consumption."""
    all_srcs = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      assert su.PYTHON_THRIFT_LIB_TYPE == other_rule_details[su.TYPE_KEY]
      all_srcs.append(other_rule_details[su.SRCS_KEY][0])
    rule_details[su.ALL_SRCS_KEY] = all_srcs

  @classmethod
  def _set_all_dep_paths(cls, rule_details, details_map):
    """Set all dependency paths."""
    all_dep_paths = rule_details[su.ALL_SRCS_KEY][:]
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      assert su.PYTHON_THRIFT_LIB_TYPE == other_rule_details[su.TYPE_KEY]
      all_dep_paths.append(other_rule_details[su.OUT_KEY])
    all_dep_paths.append(rule_details[su.OUT_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(list(set(all_dep_paths)))

  def setup(self, rule_details, details_map):
    """Full setup using details map."""
    su.init_rule_common(rule_details, rule_details[su.NAME_KEY], [su.SRCS_KEY])
    super(PyThriftLibrary, self).setup(rule_details, details_map)
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    self._set_all_srcs(rule_details, details_map)
    self._set_all_dep_paths(rule_details, details_map)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = cls._get_work_dirs(rule_details)
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[tc.SRC_CODE_DIR]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.append(tc.get_thrift_compile_command(
        rule_details, rule_details[tc.GEN_CODE_DIR]))
    command_list.append([su.CHANGE_CURR_DIR, rule_details[tc.GEN_CODE_DIR]])
    # Thrift generates the root level module definition file that conflicts with
    # pylint. This is not a problem downstream since we fill in our own
    # __main__.py in this directory later.
    command_list.append(['rm', './__init__.py'])
    tmp_out_file = os.path.join(rule_details[su.WDIR_KEY],
                                '.tmp.' + rule_details[su.NAME_KEY])
    command_list.append(
        [su.PYTHON_LINK_ALL, su.PYTHON_LIB_TYPE,
         su.PYTHON_FAKE_MAIN_METHOD, tmp_out_file, rule_details[su.OUT_KEY]])
    return command_list
