"""Rules for cc thrift libraries.

For a given sample.thrift file, thrift compiler generates:
    - sample_constants.{cpp,h} + sample_types.{cpp,h} : Always generated
    - SomeService.{cpp,h} + SomeService_server.skeleton.cpp : If sample.thrift
      has some service definition.

Final rule outcome is set of header files and an object file made by merging
all the above cpp files into one except unwanted skeleton file.

Note: If the service names found by parsing thrift file and those generated by
thrift compile don't match, the build fails.
"""
import logging
import os
import mool.shared_utils as su
import mool.thrift.thrift_common as tc


SKELETON_FILE_SUFFIX = '_server.skeleton.cpp'


def assert_check_services(cpp_files):
  """Checks if the given list of cpp files is complete list of expected
  cpp files. This check ensures that we parsed all the service names correctly
  from thrift source file."""
  cpp_files = [os.path.basename(cpp_file) for cpp_file in cpp_files[0]]
  gen_files = [f for f in os.listdir('.')
               if f.endswith('.cpp') and not f.endswith(SKELETON_FILE_SUFFIX)]
  if not sorted(gen_files) == sorted(cpp_files):
    msg = ('Expected list of cpp files: {}\nGenerated list of cpp files: {}\n'
           'Your generated services should match "{}" pattern and make sure '
           'you don\'t have services in commented section!')
    msg = msg.format(cpp_files, gen_files, tc.THRIFT_SERVICE_PATTERN_STRING)
    raise su.Error(msg)


class CplusplusThrift(tc.ThriftCommon):
  """Class for handling thrift cc lib rule."""
  @classmethod
  def _get_generated_file_names(cls, rule_details, extention):
    """Returns names of all the generated files. Use this to get names of
    all cpp and header files."""
    file_prefix = cls._get_thrift_file_prefix(rule_details)
    services = cls._get_services_list(rule_details)
    file_names = ['{}_types'.format(file_prefix),
                  '{}_constants'.format(file_prefix)]
    file_names.extend(services)
    return ['{}{}'.format(name, extention) for name in file_names]

  @classmethod
  def _set_expected_output(cls, rule_details):
    """Sets the expected lib and header out files."""
    out_dir = rule_details[su.OUTDIR_KEY]
    obj_files = cls._get_generated_file_names(rule_details, '.o')
    rule_details[su.OUT_KEY] = [os.path.join(out_dir, f) for f in obj_files]

    # All the headers are emitted at OUT_HEADERS_DIR_KEY path.
    rule_details[su.OUT_HEADERS_DIR_KEY] = os.path.join(
        out_dir, rule_details[su.PATH_SUBDIR_KEY])
    # For the easy of accessing all header files, we set this key.
    header_out_dir = rule_details[su.OUT_HEADERS_DIR_KEY]
    header_files = cls._get_generated_file_names(rule_details, '.h')
    rule_details[su.OUT_HEADERS_KEY] = [
        os.path.join(header_out_dir, header) for header in header_files]

  @classmethod
  def _set_all_srcs(cls, rule_details, details_map):
    """Set all sources to be added in gcc compiler command line."""
    all_srcs = []
    current_rule_symbol = rule_details[su.SYMBOL_KEY]
    # We need to copy/symlink the headers of deps in this rules working
    # directory and so we append the deps headers out dir in possible prefixes.
    prefixes = []
    for rule_symbol in rule_details[su.ALL_DEPS_KEY]:
      dep_rule = details_map[rule_symbol]
      all_srcs.extend(dep_rule[su.SRCS_KEY])
      if current_rule_symbol != rule_symbol:
        all_srcs.extend(dep_rule[su.OUT_HEADERS_KEY])
        prefixes.append(dep_rule[su.OUTDIR_KEY])
    rule_details[su.ALL_SRCS_KEY] = sorted(list(set(all_srcs)))
    rule_details[su.POSSIBLE_PREFIXES_KEY].extend(
        [os.path.join(prefix, '') for prefix in prefixes])

  @classmethod
  def _set_all_dep_paths(cls, rule_details):
    """Set all dependency paths."""
    all_dep_paths = rule_details[su.ALL_SRCS_KEY][:]
    all_dep_paths.extend(rule_details[su.OUT_KEY])
    all_dep_paths.extend(rule_details[su.OUT_HEADERS_KEY])
    rule_details[su.ALL_DEP_PATHS_KEY].extend(all_dep_paths)
    rule_details[su.ALL_DEP_PATHS_KEY] = sorted(
        list(set(rule_details[su.ALL_DEP_PATHS_KEY])))

  @classmethod
  def _compile_gen_code_cmd(cls, rule_details, src_files):
    """Get command to compile merged c++ files."""
    compile_command = su.CC_COMPILER.split()
    # We copy all the headers + thrift files of deps in SRC_CODE_DIR and all
    # generated headers of this rule in OUT_HEADERS_DIR_KEY. Since the
    # generated source files refer to headers using full path, we add OUTDIR
    # as well in g++ path.
    compile_command.extend([
        '-c', '-isystem', '.', '-isystem', su.CC_THRIFT_INCDIR,
        '-isystem', su.CC_BOOST_INCDIR, '-I', rule_details[tc.SRC_CODE_DIR],
        '-I', rule_details[su.OUTDIR_KEY]])
    compile_command.extend(src_files)
    return compile_command

  def setup(self, rule_details, details_map):
    """Full setup using details map."""
    su.init_rule_common(rule_details, None, [su.SRCS_KEY])
    rule_details[su.POSSIBLE_PREFIXES_KEY] = su.prefix_transform([])
    super(CplusplusThrift, self).setup(rule_details, details_map)
    self._validate(rule_details, details_map)
    self._set_expected_output(rule_details)
    self._set_all_srcs(rule_details, details_map)
    self._set_all_dep_paths(rule_details)

  @classmethod
  def build_commands(cls, rule_details):
    """Generate build command line."""
    logging.info(
        'Emitting %s lib and headers in dir: %s',
        rule_details[su.TYPE_KEY],
        su.log_normalize(rule_details[su.OUTDIR_KEY]))

    directory_list = cls._get_work_dirs(rule_details)
    directory_list.append(rule_details[su.OUT_HEADERS_DIR_KEY])
    gen_code_dir = cls._get_gen_code_dir(rule_details)
    header_files = cls._get_generated_file_names(rule_details, '.h')
    cpp_files = cls._get_generated_file_names(rule_details, '.cpp')
    obj_files = cls._get_generated_file_names(rule_details, '.o')

    command_list = [su.get_mkdir_command(d) for d in directory_list]
    # Generate code using thrift compiler and copy headers to out directory.
    command_list.append([su.CHANGE_CURR_DIR, rule_details[tc.SRC_CODE_DIR]])
    command_list.extend(su.cp_commands_list(rule_details, su.ALL_SRCS_KEY))
    command_list.append(tc.get_thrift_compile_command(
        rule_details, rule_details[tc.GEN_CODE_DIR]))
    command_list.append([su.CHANGE_CURR_DIR, gen_code_dir])
    command_list.append([su.THRIFT_CHECK_GENERATED_SOURCE, cpp_files])
    command_list.extend([['cp', h, os.path.join(
        rule_details[su.OUT_HEADERS_DIR_KEY], h)] for h in header_files])
    # Compile generated code
    command_list.append(cls._compile_gen_code_cmd(rule_details, cpp_files))
    command_list.extend([['cp', o, os.path.join(
        rule_details[su.OUTDIR_KEY], o)] for o in obj_files])
    return command_list
