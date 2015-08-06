"""Implement the rules of each C++ build utility type."""
import logging
import os
import sys

import mool.shared_utils as su


CC_EXECUTABLE_TYPES = (su.CC_BIN_TYPE, su.CC_TEST_TYPE)
CC_LIB_EXPORTER_TYPES = (su.CC_PROTO_LIB_TYPE)
CC_MULTIPLE_LIB_EXPORTER_TYPES = (su.CC_LIB_TYPE, su.CC_THRIFT_LIB_TYPE)


def sort_gcc_link_libs(link_libs):
  """gcc's dumb linker needs the link libraries in proper order for the
  compilation to work. General rule of thumb if a depends on b then a comes
  before b on command line."""
  # .o files first, then .a files and then remaining files. We may want to get
  # rid of .a files as its difficult to find dependency order b/w them.
  object_files = [lib for lib in link_libs if lib.endswith('.o')]
  archives = [lib for lib in link_libs if lib.endswith('.a')]
  other_libs = [lib for lib in link_libs
                if not lib in object_files and not lib in archives]
  arranged_libs = list(object_files)
  arranged_libs.extend(archives)
  arranged_libs.extend(other_libs)
  return arranged_libs


def _get_obj_file_name(src_file):
  """Returns name of object file from cc source file."""
  src_file = os.path.basename(src_file)
  return src_file.rsplit('.', 1)[0] + '.o'


def _get_obj_out_name(rule_details, src_file):
  """Returns file name to be used in output directory for obj file symlink."""
  return '{}.{}'.format(
      rule_details[su.NAME_KEY], _get_obj_file_name(src_file))


class CplusplusCommon(object):
  """Common C++ handler functions."""
  @classmethod
  def _expand_env_vars_if_needed(cls, dep_path):
    """Expand environment variable path if needed."""
    if not dep_path.startswith(su.PC_DEPS_PREFIX):
      return dep_path
    return su.expand_env_vars(dep_path)

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
      # cc_thrift_lib and cc_lib emit multiple .o files.
      rule_type = details_map[rule_symbol][su.TYPE_KEY]
      if rule_type in CC_LIB_EXPORTER_TYPES:
        link_libs.append(details_map[rule_symbol][su.OUT_KEY])
      elif rule_type in CC_MULTIPLE_LIB_EXPORTER_TYPES:
        link_libs.extend(details_map[rule_symbol][su.OUT_KEY])
    sys_deps = [cls._expand_env_vars_if_needed(s)
                for s in sorted(list(set(sys_deps)))]

    # Linked libs are the .o files from dependency lib rule outputs.
    assert len(set(link_libs)) == len(link_libs)
    assert all([l.endswith('.o') for l in link_libs])

    # Precompiled linked libs are picked only from current dependency.
    pc_link_libs = rule_details[su.PC_DEPS_KEY]
    assert len(set(pc_link_libs)) == len(pc_link_libs)

    link_libs.extend(pc_link_libs)
    all_link_libs.extend(link_libs)
    all_link_libs.extend(sys_deps)
    # Some C++ libraries need additional flag "-lrt" to build successfully on
    # CentOS. This flag is not needed on Mac OS. At this point in time we do not
    # know what is the full extent of dissimilarities between Linux and Mac OS
    # C++ code building. The following is a temporary hack to workaround.
    # TODO: Build a better solution for this hack once the problem is better
    # understood.
    if (((not su.TEST_MODE_EXECUTION) and
         (rule_details[su.TYPE_KEY] in CC_EXECUTABLE_TYPES) and
         (sys.platform.startswith('linux2')))):
      all_link_libs.append('-lrt')
    return link_libs, all_link_libs

  @classmethod
  def _set_compile_command(cls, rule_details, all_link_libs):
    """Sets C++ compile command."""
    # Nothing to do in case there is no source file. Such a rule is used to
    # collect header files in one place.
    if not rule_details[su.SRCS_KEY]:
      return

    if all((f.endswith('.c') for f in rule_details[su.SRCS_KEY])):
      compile_command = su.CC_COMPILER.replace('g++', 'gcc').split()
    else:
      compile_command = su.CC_COMPILER.split()

    compile_command.extend(['-isystem', '.'])
    for other_dir in rule_details[su.OTHER_INCLUDE_DIRS]:
      if other_dir.startswith(su.PC_DEPS_PREFIX):
        other_dir = su.expand_env_vars(other_dir)
      compile_command.extend(['-isystem', other_dir])
    for other_dir in rule_details[su.OTHER_LIB_DIRS]:
      if other_dir.startswith(su.PC_DEPS_PREFIX):
        other_dir = su.expand_env_vars(other_dir)
      compile_command.append('-L{}'.format(other_dir))
    compile_command.extend(rule_details[su.COMPILE_PARAMS_KEY])
    compile_command.extend(
        [su.get_relative_path(rule_details[su.POSSIBLE_PREFIXES_KEY], f)
         for f in rule_details[su.SRCS_KEY]])
    compile_command.extend(sort_gcc_link_libs(all_link_libs))
    if cls._get_out_file(rule_details):
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
  def _apply_protobuf_thrift_deps(cls, rule_details, details_map):
    """Set compile dependencies if this lib depends on proto or thrift libs."""
    has_proto = False
    has_thrift = False
    all_hdrs = []
    link_libs = []
    # We need to copy the headers of any thrift dependencies we generate and
    # so we add the base out directory of thrift lib rules to prefixes list.
    prefixes = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      other_rule_details = details_map[rule_symbol]
      if other_rule_details[su.TYPE_KEY] == su.CC_PROTO_LIB_TYPE:
        all_hdrs.extend(other_rule_details[su.HDRS_KEY])
        has_proto = True
      elif other_rule_details[su.TYPE_KEY] == su.CC_THRIFT_LIB_TYPE:
        all_hdrs.extend(other_rule_details[su.OUT_HEADERS_KEY])
        prefixes.append(other_rule_details[su.OUTDIR_KEY])
        has_thrift = True
      else:
        all_hdrs.extend(other_rule_details[su.HDRS_KEY])
    # Set protobuf header and library dependencies.
    if has_proto:
      rule_details[su.OTHER_INCLUDE_DIRS].append(
          os.path.join(su.CC_INSTALL_PREFIX, 'include'))
      if rule_details[su.TYPE_KEY] in CC_EXECUTABLE_TYPES:
        rule_details[su.OTHER_LIB_DIRS].append(
            os.path.join(su.CC_INSTALL_PREFIX, 'lib'))
        link_libs.extend(['-lprotobuf', '-lpthread', '-pthread'])
    # Set thrift header and library dependencies.
    if has_thrift:
      rule_details[su.OTHER_INCLUDE_DIRS].append(su.CC_THRIFT_INCDIR)
      rule_details[su.OTHER_INCLUDE_DIRS].append(su.CC_BOOST_INCDIR)
      if rule_details[su.TYPE_KEY] in CC_EXECUTABLE_TYPES:
        rule_details[su.OTHER_LIB_DIRS].append(su.CC_THRIFT_LIBDIR)
        link_libs.append('-lthrift')
    rule_details[su.POSSIBLE_PREFIXES_KEY].extend(su.prefix_transform(prefixes))
    return all_hdrs, link_libs

  @classmethod
  def _apply_dependencies(cls, rule_details, details_map, link_libs,
                          all_link_libs):
    """Gets all direct requirements."""
    all_hdrs, idl_link_libs = cls._apply_protobuf_thrift_deps(
        rule_details, details_map)
    rule_details[su.ALL_SRCS_KEY] = list(rule_details[su.SRCS_KEY])
    rule_details[su.ALL_SRCS_KEY].extend(all_hdrs)
    all_dep_paths = rule_details[su.ALL_SRCS_KEY][:]
    all_dep_paths.extend(link_libs)
    if rule_details[su.TYPE_KEY] == su.CC_LIB_TYPE:
      all_dep_paths.extend(rule_details[su.OUT_KEY])
    else:
      all_dep_paths.append(rule_details[su.OUT_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(list(set(all_dep_paths)))
    all_link_libs.extend(idl_link_libs)
    all_link_libs = sorted(list(set(all_link_libs)))
    rule_details[su.OTHER_INCLUDE_DIRS] = sorted(
        list(set(rule_details[su.OTHER_INCLUDE_DIRS])))
    rule_details[su.OTHER_LIB_DIRS] = sorted(
        list(set(rule_details[su.OTHER_LIB_DIRS])))
    cls._set_compile_command(rule_details, all_link_libs)

  @classmethod
  def _get_out_file(cls, rule_details):
    """Get outfile name from rule type."""
    # There can be multiple .o files in case of cc_lib rule.
    if rule_details[su.TYPE_KEY] != su.CC_LIB_TYPE:
      return rule_details[su.NAME_KEY]

  @classmethod
  def _set_compile_params(cls, rule_details, compile_params):
    """Set compile params."""
    rule_details[su.COMPILE_PARAMS_KEY] = compile_params or []

  @classmethod
  def _internal_setup(cls, rule_details, details_map):
    """Initializing build rule dictionary."""
    rule_details[su.OTHER_INCLUDE_DIRS] = rule_details.get(
        su.OTHER_INCLUDE_DIRS, [])
    rule_details[su.OTHER_LIB_DIRS] = rule_details.get(
        su.OTHER_LIB_DIRS, [])
    rule_details[su.PC_DEPS_KEY] = rule_details.get(su.PC_DEPS_KEY, [])
    rule_details[su.COMPILE_PARAMS_KEY] = rule_details.get(
        su.COMPILE_PARAMS_KEY, [])
    su.init_rule_common(rule_details, cls._get_out_file(rule_details),
                        [su.SRCS_KEY, su.HDRS_KEY])
    # In case of a cc_lib, we emit multiple .o files in work directory and link
    # the .o files in out directory.
    if rule_details[su.TYPE_KEY] == su.CC_LIB_TYPE:
      rule_details[su.OUT_KEY] = []
      for src_file in rule_details[su.SRCS_KEY]:
        out_file = os.path.join(rule_details[su.OUTDIR_KEY], _get_obj_out_name(
            rule_details, src_file))
        rule_details[su.OUT_KEY].append(out_file)
    if rule_details[su.TYPE_KEY] == su.CC_TEST_TYPE:
      test_command = su.VALGRIND_PREFIX[:]
      test_command.append(rule_details[su.OUT_KEY])
      rule_details[su.TEST_COMMANDS_KEY] = [test_command]
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform(
        [su.BUILD_OUT_DIR])
    link_libs, all_link_libs = cls._get_cc_all_link_libs(
        rule_details, details_map)
    cls._apply_dependencies(rule_details, details_map, link_libs, all_link_libs)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    directory_list = [rule_details[su.OUTDIR_KEY], rule_details[su.WDIR_KEY]]
    if rule_details[su.TYPE_KEY] == su.CC_LIB_TYPE:
      logging.info('Emitting %s objs in %s dir', rule_details[su.TYPE_KEY],
                   su.log_normalize(rule_details[su.OUTDIR_KEY]))
    else:
      logging.info('Emitting %s at %s', rule_details[su.TYPE_KEY],
                   su.log_normalize(rule_details[su.OUT_KEY]))
    command_list = [su.get_mkdir_command(d) for d in directory_list]
    command_list.append([su.CHANGE_CURR_DIR, rule_details[su.WDIR_KEY]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    # Nothing more to do if we get empty sources list.
    if not rule_details[su.SRCS_KEY]:
      return command_list
    command_list.append(rule_details[su.COMPILE_COMMAND_KEY])
    # Create link of all .o files in cwd to final output directory.
    if rule_details[su.TYPE_KEY] == su.CC_LIB_TYPE:
      for src_file in rule_details[su.SRCS_KEY]:
        obj_name = _get_obj_file_name(src_file)
        obj_path = os.path.join(rule_details[su.WDIR_KEY], obj_name)
        out_file = os.path.join(rule_details[su.OUTDIR_KEY], _get_obj_out_name(
            rule_details, src_file))
        command_list.append(su.get_copy_command(obj_path, out_file, True))
    return command_list


class CplusplusLibrary(CplusplusCommon):
  """Handler class for cc lib build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Do full setup."""
    cls._set_compile_params(rule_details, ['-c'])
    cls._internal_setup(rule_details, details_map)


class CplusplusBinary(CplusplusCommon):
  """Handler class for cc binary build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Do full setup."""
    cls._internal_setup(rule_details, details_map)


class CplusplusTest(CplusplusCommon):
  """Handler class for cc test build rules."""
  @classmethod
  def setup(cls, rule_details, details_map):
    """Do full setup."""
    cls._set_pc_deps(rule_details, ['env.GTEST_MAIN_LIB', 'env.GTEST_MOCK_LIB'])
    cls._set_compile_params(
        rule_details,
        ['-isystem', os.path.join(su.CC_INSTALL_PREFIX, 'include'), '-g',
         '-pthread'])
    cls._internal_setup(rule_details, details_map)
