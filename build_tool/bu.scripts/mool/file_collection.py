"""Implement the rules file collection build utility type."""
import logging
import os

import mool.shared_utils as su
import mool.java_common as jc
import mool.release_package as rp


class Error(su.Error):
  """Error class for this module."""


def create_archive_all_currdir(params):
  """Create archive of given type zip/jar from all files in current
  directory."""
  assert 1 == len(params)
  extension = params[0].split('.')[-1]
  if extension == 'zip':
    rp.zip_all_currdir(params)
  elif extension == 'jar':
    jc.perform_java_linkall_currdir(params)
  else:
    raise Error('Unknown extension {} while creating {}!!'.format(
        extension, params[0]))


def extract_archive_in_currdir(params):
  """Extracts archive into current working directory."""
  assert 1 == len(params)
  extension = params[0].split('.')[-1]
  if extension == 'zip':
    rp.unzip_all_currdir(params[0])
  elif extension == 'jar':
    su.extract_all_currdir(params[0])
  else:
    raise Error('Unknown extension {} while extracting {}!!'.format(
        extension, params[0]))


class FileCollection(object):
  """File Collection build utility type."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Full setup using details map."""
    out_file = rule_details[su.NAME_KEY] + '.{}'.format(rule_details.get(
        su.ARCHIVE_TYPE, su.DEFAULT_FILE_COLL_ARCHIVE_TYPE))
    su.init_rule_common(rule_details, out_file, [su.SRCS_KEY])
    rule_details[su.SRCS_KEY] = rule_details.get(su.SRCS_KEY, [])
    rule_details[su.FILE_PACKAGE_KEY] = rule_details.get(
        su.FILE_PACKAGE_KEY, rule_details[su.PATH_SUBDIR_KEY])
    rule_details[su.FILE_PACKAGE_KEY] = os.path.join(
        '.', rule_details[su.FILE_PACKAGE_KEY])
    all_dep_paths = rule_details[su.SRCS_KEY][:]
    all_dep_paths.append(rule_details[su.OUT_KEY])
    rule_details[su.FILE_COLL_DEPS_KEY] = []
    for dep in rule_details.get(su.DEPS_KEY, []):
      dep_rule_details = details_map[dep]
      if dep_rule_details[su.TYPE_KEY] != su.FILE_COLL_TYPE:
        raise Error('Unknown dependency type for file collection.')
      all_dep_paths.append(dep_rule_details[su.OUT_KEY])
      rule_details[su.FILE_COLL_DEPS_KEY].append(dep_rule_details[su.OUT_KEY])
    if (((not rule_details[su.SRCS_KEY]) and
         (not rule_details[su.FILE_COLL_DEPS_KEY]))):
      raise Error('Unnecessary empty file collection rule.')
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
    if rule_details[su.SRCS_KEY]:
      # Only need to make the file package directory if current rule specifies
      # some sources.
      command_list.append(
          su.get_mkdir_command(rule_details[su.FILE_PACKAGE_KEY]))
    for src_file in rule_details[su.SRCS_KEY]:
      dst_file = os.path.join(rule_details[su.FILE_PACKAGE_KEY],
                              os.path.basename(src_file))
      copy_command = su.get_copy_command(src_file, dst_file, True)
      command_list.append(copy_command)
    for dep_file in rule_details[su.FILE_COLL_DEPS_KEY]:
      command_list.append([su.EXTRACT_ARCHIVE_IN_CURRDIR, dep_file])
    command_list.append([su.CREATE_ARCHIVE_ALL_CURRDIR,
                         rule_details[su.OUT_KEY]])
    return command_list
