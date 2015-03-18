"""Rules for Java protocol buffers."""
import os
import logging
import mool.java_common as jc
import mool.shared_utils as su


class Error(Exception):
  """The Exception class for this module."""


def _set_proto_data(rule_details, proto_key):
  """Set java proto fields from the proto file.

  This function is somewhat unoptimized and should be executed only from
  build_commands step which is further only executed if some change is really
  needed.
  """
  if proto_key in rule_details:
    return
  proto_source_file = rule_details[su.SRCS_KEY][0]
  search_text = '{} = '.format(proto_key)
  with open(proto_source_file, 'r') as file_object:
    for line in file_object:
      lstrip = line.strip()
      if search_text not in lstrip:
        continue
      parts = lstrip.split('"')
      assert 3 == len(parts)
      rule_details[proto_key] = parts[1]
      return
  raise Error('Cannot find {} in {}'.format(proto_key, proto_source_file))


class JavaProtoLibrary(object):
  """Proto library builder functions for Java."""
  @classmethod
  def _set_all_srcs(cls, rule_details, details_map):
    """Set all sources list for downstream consumption."""
    all_srcs = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      assert su.JAVA_PROTO_LIB_TYPE == other_rule_details[su.TYPE_KEY]
      all_srcs.append(other_rule_details[su.SRCS_KEY][0])
    all_srcs.append(rule_details[su.SRCS_KEY][0])
    rule_details[su.ALL_SRCS_KEY] = all_srcs

  @classmethod
  def _set_link_libs(cls, rule_details, details_map):
    """Set link_libs list for downstream consumption."""
    link_libs = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      assert su.JAVA_PROTO_LIB_TYPE == other_rule_details[su.TYPE_KEY]
      if rule_symbol != rule_details[su.SYMBOL_KEY]:
        link_libs.append(other_rule_details[su.OUT_KEY])
    rule_details[su.JAVA_PROTO_LINK_LIBS_KEY] = link_libs

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
    su.init_rule_common(rule_details,
                        '{}.jar'.format(rule_details[su.NAME_KEY]),
                        [su.SRCS_KEY])
    su.set_workdir_child(rule_details, su.PROTO_SRCS_KEY, 'proto_src')
    su.set_workdir_child(rule_details, su.PROTO_OUTDIR_KEY, 'proto_outfiles')
    su.set_workdir_child(rule_details, su.JAVAC_OUTDIR_KEY, 'javac_outdir')
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    cls._set_all_srcs(rule_details, details_map)
    cls._set_link_libs(rule_details, details_map)
    cls._set_all_dep_paths(rule_details)

  @classmethod
  def _get_java_compile_command(cls, rule_details):
    """Get the java compile command for the generated source file."""
    _set_proto_data(rule_details, su.JAVA_OUTER_CLASSNAME_KEY)
    _set_proto_data(rule_details, su.JAVA_PACKAGE_KEY)
    gen_java_file = os.path.join(
        '.', rule_details[su.JAVA_PACKAGE_KEY].replace('.', os.sep),
        '{}.java'.format(rule_details[su.JAVA_OUTER_CLASSNAME_KEY]))
    compile_libs = rule_details[su.JAVA_PROTO_LINK_LIBS_KEY][:]
    compile_libs.append(su.JAVA_PROTOBUF_JAR)
    java_compile_command = jc.get_java_compile_command(
        rule_details, compile_libs, rule_details[su.JAVAC_OUTDIR_KEY],
        [gen_java_file], False)
    return java_compile_command

  @classmethod
  def _get_java_link_commands(cls, rule_details):
    """Get the java link commands for the generated source file."""
    command_list = []
    partial_jar = os.path.join(rule_details[su.WDIR_KEY], '.temp.jar')
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.JAVAC_OUTDIR_KEY]])
    command_list.append([su.PERFORM_JAVA_LINK_ALL_CURRDIR, partial_jar])
    link_libs = rule_details[su.JAVA_PROTO_LINK_LIBS_KEY][:]
    link_libs.append(partial_jar)
    command_list.append([
        su.JAVA_LINK_JAR_COMMAND, ([], [], list(set(link_libs))),
        rule_details[su.OUT_KEY], su.JAVA_FAKE_MAIN_CLASS])
    return command_list

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY], rule_details[su.WDIR_KEY],
                      rule_details[su.PROTO_SRCS_KEY],
                      rule_details[su.PROTO_OUTDIR_KEY],
                      rule_details[su.JAVAC_OUTDIR_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.PROTO_SRCS_KEY]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.append(
        su.get_proto_compile_command(rule_details,
                                     rule_details[su.PROTO_OUTDIR_KEY]))
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.PROTO_OUTDIR_KEY]])
    command_list.append(cls._get_java_compile_command(rule_details))
    command_list.extend(cls._get_java_link_commands(rule_details))
    return command_list
