"""Implement the rules of each C++ build utility type."""
import os
import logging
import mool.shared_utils as su


class CplusplusCommon(object):
  """Common C++ handler functions."""
  @classmethod
  def _get_cc_all_link_libs(cls, rule_details, details_map):
    """Get all link libraries for a C++ build rule."""
    if su.CC_LIB_TYPE == rule_details[su.TYPE_KEY]:
      return [], []
    # Note: It might be a good idea to combine the link libraries to an archive
    # file before linking. Linker picks up only used .o files from .a files.
    # However, we want developers to keep dependencies thin (i.e. stop
    # including unused dependencies). If that happens, then building the
    # archive file is an unnecessary additional step.

    # Ignore system dependencies if they are already specified in
    # compiler parameters.
    rule_details[su.SYS_DEPS_KEY] = [
        item for item in rule_details.get(su.SYS_DEPS_KEY, [])
        if item not in rule_details[su.COMPILE_PARAMS_KEY]]

    all_link_libs = []
    link_libs, sys_deps = [], []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      sys_deps.extend(details_map[rule_symbol].get(su.SYS_DEPS_KEY, []))
      if rule_symbol == rule_details[su.SYMBOL_KEY]:
        continue
      if details_map[rule_symbol][su.TYPE_KEY] == su.CC_LIB_TYPE:
        link_libs.append(details_map[rule_symbol][su.OUT_KEY])
    sys_deps = sorted(list(set(sys_deps)))

    # Linked libs are the .o files from dependency lib rule outputs.
    assert len(set(link_libs)) == len(link_libs)
    assert all([l.endswith('.o') for l in link_libs])

    # Precompiled linked libs are picked only from current dependency.
    pc_link_libs = rule_details[su.PC_DEPS_KEY]
    assert len(set(pc_link_libs)) == len(pc_link_libs)

    link_libs.extend(pc_link_libs)
    all_link_libs.extend(link_libs)
    all_link_libs.extend(sys_deps)
    return link_libs, all_link_libs

  @classmethod
  def _set_compile_command(cls, rule_details, proto_sources, all_link_libs):
    """Sets C++ compile command."""
    compile_command = su.CC_COMPILER.split()
    compile_command.append('-I.')
    for other_dir in rule_details.get(su.OTHER_INCLUDE_DIRS, []):
      compile_command.append('-I{}'.format(other_dir))
    compile_command.extend(rule_details[su.COMPILE_PARAMS_KEY])
    compile_command.extend(
        [su.get_relative_path(rule_details[su.POSSIBLE_PREFIXES_KEY], f)
         for f in rule_details[su.SRCS_KEY]])
    compile_command.extend(
        [su.get_relative_path(rule_details[su.POSSIBLE_PREFIXES_KEY], f)
         for f in proto_sources])
    compile_command.extend(all_link_libs)
    compile_command.extend(['-o', rule_details[su.OUT_KEY]])
    rule_details[su.COMPILE_COMMAND_KEY] = compile_command

  @classmethod
  def _set_pc_deps(cls, rule_details, extra_pc_deps):
    """Set precompiled dependency flags."""
    pc_deps = rule_details.get(su.PC_DEPS_KEY, [])
    pc_deps.extend(extra_pc_deps or [])
    pc_deps = sorted(list(set(pc_deps)))
    rule_details[su.PC_DEPS_KEY] = [su.expand_env_vars(d) for d in pc_deps]

  @classmethod
  def _set_possible_prefixes(cls, rule_details, details_map):
    """Set possible prefixes list for copying files in working directory."""
    possible_prefixes = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      if other_rule_details[su.TYPE_KEY] != su.CC_PROTO_LIB_TYPE:
        continue
      # If C++ module has proto dependencies, then the generated pb.cc and
      # pb.h files need to be copied in locally.
      possible_prefixes.extend([other_rule_details[su.WDIR_KEY]])
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform(
        possible_prefixes)

  @classmethod
  def _get_all_direct_srcs(cls, rule_details, details_map):
    """Gets all direct requirements."""
    all_hdrs = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      all_hdrs.extend(details_map[rule_symbol][su.HDRS_KEY])
    all_srcs = []
    all_srcs.extend(rule_details[su.SRCS_KEY])
    all_srcs.extend(all_hdrs)
    return all_srcs

  @classmethod
  def _get_proto_info(cls, rule_details, details_map):
    """Get information from proto dependencies."""
    proto_sources = []
    proto_dep_paths = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      if other_rule_details[su.TYPE_KEY] != su.CC_PROTO_LIB_TYPE:
        continue
      proto_sources.append(other_rule_details[su.OUT_CC_KEY])
      proto_dep_paths.append(other_rule_details[su.OUT_CC_KEY])
      proto_dep_paths.append(other_rule_details[su.OUT_HEADER_KEY])
    return proto_sources, proto_dep_paths

  @classmethod
  def _set_all_dep_paths(cls, rule_details, link_libs, proto_dep_paths):
    """Set all dependency paths used for build state check."""
    all_dep_paths = rule_details[su.ALL_SRCS_KEY][:]
    all_dep_paths.extend(link_libs)
    all_dep_paths.append(rule_details[su.OUT_KEY])
    all_dep_paths.extend(proto_dep_paths)
    rule_details[su.ALL_DEP_PATHS_KEY].extend(list(set(all_dep_paths)))

  @classmethod
  def _internal_setup(cls, rule_details, details_map, init_params):
    """Initializing build rule dictionary."""
    out_file, is_test, extra_pc_deps, compile_params = init_params
    su.init_rule_common(rule_details, out_file, [su.SRCS_KEY, su.HDRS_KEY])
    rule_details[su.COMPILE_PARAMS_KEY] = compile_params or []
    cls._set_pc_deps(rule_details, extra_pc_deps)
    if not rule_details[su.SRCS_KEY]:
      rule_details[su.SRCS_KEY] = [su.DUMMY_CC]
    if is_test:
      rule_details[su.TEST_COMMANDS_KEY] = [[rule_details[su.OUT_KEY]]]
    cls._set_possible_prefixes(rule_details, details_map)
    link_libs, all_link_libs = cls._get_cc_all_link_libs(
        rule_details, details_map)
    all_srcs = cls._get_all_direct_srcs(rule_details, details_map)
    rule_details[su.ALL_SRCS_KEY] = all_srcs
    proto_sources, proto_dep_paths = cls._get_proto_info(
        rule_details, details_map)
    rule_details[su.PROTO_SRCS_KEY] = proto_sources
    cls._set_all_dep_paths(rule_details, link_libs, proto_dep_paths)
    cls._set_compile_command(rule_details, proto_sources, all_link_libs)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    # Build system does not rebuild a rule if the file cache is current. We use
    # this optimization to perform a delayed calculation of the build command
    # list.
    logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                 su.log_normalize(rule_details[su.OUT_KEY]))
    directory_list = [rule_details[su.OUTDIR_KEY], rule_details[su.WDIR_KEY]]
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.WDIR_KEY]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.extend(su.cp_commands_list(rule_details, su.PROTO_SRCS_KEY))
    command_list.append(rule_details[su.COMPILE_COMMAND_KEY])
    return command_list


class CplusplusLibrary(CplusplusCommon):
  """Handler class for CC lib build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Do full setup."""
    init_params = (
        '{}.o'.format(rule_details[su.NAME_KEY]), False, None, ['-c'])
    cls._internal_setup(rule_details, details_map, init_params)


class CplusplusBinary(CplusplusCommon):
  """Handler class for CC binary build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Do full setup."""
    init_params = (rule_details[su.NAME_KEY], False, None, [])
    cls._internal_setup(rule_details, details_map, init_params)


class CplusplusTest(CplusplusCommon):
  """Handler class for CC test build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Do full setup."""
    init_params = (
        rule_details[su.NAME_KEY], True,
        ['env.GTEST_MAIN_LIB', 'env.GTEST_MOCK_LIB'],
        ['-isystem', os.path.join(su.GMOCK_DIR, 'include'), '-isystem',
         os.path.join(su.GTEST_DIR, 'include'), '-pthread'])
    cls._internal_setup(rule_details, details_map, init_params)
