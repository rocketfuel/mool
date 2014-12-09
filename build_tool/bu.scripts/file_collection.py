"""Implement the rules file collection build utility type."""
import logging
import os

import shared_utils as su


class FileCollection(object):
  """File Collection build utility type."""
  @classmethod
  def setup(cls, rule_details, _unused_details_map):
    """Full setup using details map."""
    out_file = rule_details[su.NAME_KEY] + '.jar'
    su.init_rule_common(rule_details, out_file, [su.SRCS_KEY])
    rule_details[su.FILE_PACKAGE_KEY] = rule_details.get(
        su.FILE_PACKAGE_KEY, rule_details[su.PATH_SUBDIR_KEY])
    rule_details[su.FILE_PACKAGE_KEY] = os.path.join(
        '.', rule_details[su.FILE_PACKAGE_KEY])
    all_dep_paths = rule_details[su.SRCS_KEY][:]
    all_dep_paths.append(rule_details[su.OUT_KEY])
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    rule_details[su.ALL_DEP_PATHS_KEY] = sorted(list(set(all_dep_paths)))

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.WDIR_KEY]])
    command_list.append(su.get_mkdir_command(rule_details[su.FILE_PACKAGE_KEY]))
    for src_file in rule_details.get(su.SRCS_KEY, []):
      dst_file = os.path.join(rule_details[su.FILE_PACKAGE_KEY],
                              os.path.basename(src_file))
      copy_command = su.get_copy_command(src_file, dst_file, True)
      command_list.append(copy_command)
    command_list.append([su.PERFORM_JAVA_LINK_ALL_CURRDIR,
                         rule_details[su.OUT_KEY]])
    return command_list
