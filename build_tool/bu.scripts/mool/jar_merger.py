"""Jar merger utility."""
import os
import subprocess
import zipfile

import mool.shared_utils as su


MANIFEST_SERVICES_PREFIX = os.path.join(
    su.JAR_MANIFEST_KEY, su.JAR_MANIFEST_SERVICE_KEY, '')


class Error(su.Error):
  """The exception class for this module."""


def _raise_warning(msg):
  """Raise warning with given message."""
  if su.is_developer_mode():
    print 'WARN: {}'.format(msg)


@su.report_timing
def check_jar_collisions(jar_list):
  """Check if there is any collision among the classes of given jar list."""
  class_map = {}
  clashes_found = False
  for jar_file in jar_list:
    with zipfile.ZipFile(jar_file, 'r') as jar_obj:
      for cfile in sorted(jar_obj.namelist()):
        if cfile.startswith('META-INF') or not cfile.endswith('.class'):
          continue
        crc = jar_obj.getinfo(cfile).CRC
        if cfile not in class_map:
          class_map[cfile] = (crc, jar_file)
        elif class_map[cfile][0] != crc:
          clashes_found = True
          msg = 'Same file {} with different content found in jars {} & {}!'
          msg = msg.format(cfile, os.path.realpath(jar_file),
                           os.path.realpath(class_map[cfile][1]))
          # TODO: We may want to change this to error in future!
          _raise_warning(msg)
  return clashes_found


def _common_prefix(str1, str2):
  """Check if one string is a prefix of other."""
  if str1.startswith(str2) or str2.startswith(str1):
    return True
  return False


def _allowed(src_file, inclusions, exclusions):
  """Is this source file allowed under given inclusions & exclusions?"""
  if any([src_file.startswith(e) for e in exclusions]):
    return False
  # We want to match the "directories" as well having a given file.
  if any([_common_prefix(src_file, i) for i in inclusions]):
    return True
  # Allow the files inside META-INF/services/*.
  if all([src_file.startswith(MANIFEST_SERVICES_PREFIX),
          src_file != MANIFEST_SERVICES_PREFIX]):
    return True
  # No inclusions given, take it unless its any unwanted junk in META-INF/.
  if not inclusions and not src_file.startswith(su.JAR_MANIFEST_KEY):
    return True
  return False


class JarMerger(object):
  """Jar merger utility class."""
  def __init__(self, params):
    """Initializer."""
    self.manifest_services = {}
    self.file_hash_dict = {}
    self.file_src_dict = {}
    (self.jar_files, self.inclusions, self.exclusions,
     self.jar_out_file) = params

  @classmethod
  def _read_file_from_archive(cls, read_obj, src_file):
    """Read entire file contents from archive to memory."""
    with read_obj.open(src_file, 'r') as file_obj:
      return file_obj.read()

  @classmethod
  def _write_target_file(cls, write_obj, src_file, file_text):
    """Write text to target file."""
    if src_file.endswith(os.sep) and not file_text:
      write_obj.writestr(src_file, file_text)
    else:
      write_obj.writestr(src_file, file_text, zipfile.ZIP_DEFLATED)

  def _copy_file_obj(self, write_obj, jar_file, read_obj, src_file):
    """Utility to copy file from source archive to destination archive."""
    file_hash = read_obj.getinfo(src_file).CRC
    if src_file not in self.file_hash_dict:
      with read_obj.open(src_file, 'r') as src_obj:
        # Python standard zipfile library doesn't allow appending to an
        # existing file in zip. For now we read whole file in memory and write
        # it back.
        self._write_target_file(write_obj, src_file, src_obj.read())
      self.file_hash_dict[src_file] = file_hash
    elif self.file_hash_dict[src_file] != file_hash:
      raise Error(
          'File clash: Mismatching "{}" exists in both {} and {}'.format(
              src_file, self.file_src_dict[src_file], jar_file))
    else:
      # There was a duplicate with the same hash. Ignore and continue.
      pass

  def _copy_src_file(self, write_obj, jar_file, read_obj, src_file):
    """Copy the src_file from source jar (read_obj) to the target jar
    (write_obj)."""
    if not _allowed(src_file, self.inclusions, self.exclusions):
      return
    if src_file.startswith(MANIFEST_SERVICES_PREFIX):
      if src_file not in self.manifest_services:
        self.manifest_services[src_file] = []
      self.manifest_services[src_file].append(
          self._read_file_from_archive(read_obj, src_file))
    else:
      self._copy_file_obj(write_obj, jar_file, read_obj, src_file)

  def _merge_manifests(self, write_obj):
    """Merge manifest files to output archive."""
    def _get_lines(file_text):
      """Removes commented and blank lines in a file and returns a list."""
      return set([line for line in file_text.split('\n')
                  if not line.startswith('#') and line])

    if self.manifest_services:
      self._write_target_file(
          write_obj, os.path.join(MANIFEST_SERVICES_PREFIX, ''), '')
    for src_file, services in self.manifest_services.iteritems():
      lines = []
      for file_text in services:
        lines.extend(_get_lines(file_text))
      self._write_target_file(write_obj, src_file, '\n'.join(lines))

  def merge(self, main_class):
    """Actual merge operation."""
    need_main = (main_class != su.JAVA_FAKE_MAIN_CLASS)
    # No need for complicated linking under certain conditions.
    copy_ok = ((not need_main) and (1 == len(self.jar_files)) and
               (not self.inclusions) and (not self.exclusions))
    if copy_ok:
      subprocess.check_call(
          su.get_copy_command(
              self.jar_files[0], self.jar_out_file,
              su.is_temporary_path(self.jar_out_file)))
      return
    self.manifest_services = {}
    with zipfile.ZipFile(self.jar_out_file, 'w') as write_obj:
      self._write_target_file(
          write_obj, os.path.join(su.JAR_MANIFEST_KEY, ''), '')
      for jar_file in self.jar_files:
        with zipfile.ZipFile(jar_file, 'r') as read_obj:
          for src_file in sorted(read_obj.namelist()):
            self._copy_src_file(write_obj, jar_file, read_obj, src_file)
            self.file_src_dict[src_file] = jar_file
      self._merge_manifests(write_obj)
    # Finally pre-process once using the jar tool to make it look official.
    if need_main:
      subprocess.check_call([su.JAR_BIN, 'ufe', self.jar_out_file, main_class])
    else:
      subprocess.check_call([su.JAR_BIN, 'umf', os.devnull, self.jar_out_file])


def do_merge(lib_details, jar_out_file, main_class):
  """Merge jar files."""
  inclusions, exclusions, jar_files = lib_details
  assert su.path_exists(os.path.dirname(jar_out_file))
  assert all([su.path_exists(f) for f in jar_files])
  assert 1 <= len(jar_files)
  params = jar_files, inclusions, exclusions, jar_out_file
  JarMerger(params).merge(main_class)
