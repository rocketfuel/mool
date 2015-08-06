"""Script to setup an eclipse project from mool compatible java codebase.

It does following:
    * Finds all BLD files from given list of include source directories.
    * Runs bu do_build for each of the BLD file and picks the dependencies
      from builder object and determines set of jars to be added in eclipse
      project dependency.
    * Creates project by given name in eclipse workspace and creates a link
      to src_root in workspace project directory.

For all the java maven libs, we try to attach their corresponding sources.
"""
from xml.dom import minidom

import argparse
import os
import sys
import xml.etree.ElementTree as ET

import mool.core_cmds as cc
import mool.java_common as jc
import mool.shared_utils as su

try:
  BUILD_ROOT = os.environ['BUILD_ROOT']
except KeyError as exc:
  print 'BUILD_ROOT environment variable not set.'
  print 'Configure mool build environment before running this script!!'
  sys.exit(1)


BUILD_OUT_DIR = os.environ['BUILD_OUT_DIR']
CLASSPATH_FILE = '.classpath'
JAVA_SRC_EXTENSION = '.java'
PROJECT_FILE = '.project'
WORKSPACE_KEY = 'ECLIPSE_WORKSPACE_DIR'

PROJECT_FILE_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
  <name>{NAME}</name>
  <comment></comment>
  <projects>
  </projects>
  <buildSpec>
    <buildCommand>
      <name>org.eclipse.jdt.core.javabuilder</name>
      <arguments>
      </arguments>
    </buildCommand>
  </buildSpec>
  <natures>
    <nature>org.eclipse.jdt.core.javanature</nature>
  </natures>
</projectDescription>"""


class Error(Exception):
  """Error class for this module."""


def _parse_command_line(program_name, cmd_line):
  """Command line arguments parser."""
  arg_parser = argparse.ArgumentParser(prog=program_name, epilog=(
      'NOTE: All paths should either be absolute or relative to BUILD_ROOT.'))
  arg_parser.add_argument('-p', '--project_name', required=True,
                          help='project name to use for new eclipse project')
  arg_parser.add_argument('-i', '--include_srcs', nargs='+', required=True,
                          help='list of directories to import in project')
  arg_parser.add_argument('-e', '--exclude_srcs', nargs='+', default=[],
                          help='list of source directories to exclude')
  arg_parser.add_argument('-r', '--src_root', default='java',
                          help='java source root directory')
  workspace_help = 'eclipse workspace directory path (or env.{})'.format(
      WORKSPACE_KEY)
  arg_parser.add_argument('-w', '--workspace_dir', default=None,
                          help=workspace_help)
  return arg_parser.parse_args(cmd_line)


def _get_java_proto_jar():
  """Returns path of java protobuf jar."""
  return su.JAVA_PROTOBUF_JAR


def _extract_jar_list(builder):
  """Get list of all relevant java lib jars. To avoid jar repetition we just
  add java proto jars, jars from maven rules and java libs from source."""
  # List of tuples of java_lib out jar and corresponding source (default None)
  # TODO: Handle dependency on other languages like scala/clojure.
  jar_list = []
  for _, details in builder.get_rules_map().iteritems():
    if su.MAVEN_SPECS_KEY in details:
      specs = details[su.MAVEN_SPECS_KEY]
      args = (specs[su.MAVEN_ARTIFACT_ID_KEY],
              specs.get(su.MAVEN_CLASSIFIER_KEY, ''),
              specs[su.MAVEN_GROUP_ID_KEY],
              specs[su.MAVEN_REPO_URL_KEY],
              specs[su.MAVEN_VERSION_KEY])
      paths = jc.get_maven_download_paths(args)
      if not os.path.exists(paths[1]):
        raise Error('Maven jar %s not found!', paths[1])
      src_path = paths[3] if os.path.exists(paths[3]) else None
      jar_list.append((paths[1], src_path))
    elif details[su.TYPE_KEY] == su.JAVA_LIB_TYPE:
      jar_list.append((details[su.OUT_KEY], None))
    elif details[su.TYPE_KEY] == su.JAVA_PROTO_LIB_TYPE:
      jar_list.append((details[su.OUT_KEY], None))
      jar_list.append((_get_java_proto_jar(), None))
  return list(set(jar_list))


def _write_file(data, file_path):
  """Write data to at given file path."""
  with open(file_path, 'w', 'utf-8') as file_obj:
    file_obj.write(data)


def _generate_xml_file(file_path, root_elem):
  """Writes a pretty xml tree to file_path."""
  xml_string = ET.tostring(root_elem)
  with open(file_path, 'w') as xml_obj:
    xml_obj.write(minidom.parseString(xml_string).toprettyxml(indent='    '))


def _generate_project_file(dir_path, project_name):
  """Generate eclipse .project file at given directory path."""
  data = PROJECT_FILE_DATA.format(NAME=project_name)
  with open(os.path.join(dir_path, PROJECT_FILE), 'w') as file_obj:
    file_obj.write(data)


def _generate_classpath_file(out_dir, include_srcs, exclude_srcs, src_root,
                             jar_files):
  """Generate eclipse .classpath file from given parameters."""
  root_elem = ET.Element('classpath')
  root_elem.append(ET.Element('classpathentry', attrib={
      'kind': 'output', 'path': 'bin'}))
  root_elem.append(ET.Element('classpathentry', attrib={
      'kind': 'con', 'path': 'org.eclipse.jdt.launching.JRE_CONTAINER'}))

  rel_src_root = os.path.relpath(src_root, BUILD_ROOT)
  includes = []
  excludes = []
  for src in include_srcs:
    rel_path = os.path.relpath(src, src_root)
    includes.append(rel_path + '/' if os.path.isdir(src) else rel_path)
  for src in exclude_srcs:
    rel_path = os.path.relpath(src, src_root)
    excludes.append(rel_path + '/' if os.path.isdir(src) else rel_path)
  attribs = {
      'kind': 'src', 'path': rel_src_root, 'including': '|'.join(includes)}
  if excludes:
    attribs['excluding'] = '|'.join(excludes)
  root_elem.append(ET.Element('classpathentry', attrib=attribs))

  for jar_file, src_file in jar_files:
    attribs = {'kind': 'lib', 'path': jar_file}
    if src_file and os.path.exists(src_file):
      attribs['sourcepath'] = src_file
    root_elem.append(ET.Element('classpathentry', attrib=attribs))
  _generate_xml_file(os.path.join(out_dir, CLASSPATH_FILE), root_elem)


def _build_all_rules(bld_files):
  """Build all rules in given list of BLD files and return the set of jars
  along with their corresponding source libraries (if available).
  We skip jars of java rules whose sources are being added to eclipse."""
  jar_list = []
  for bld_file in bld_files:
    rule_symbol = su.get_rule_symbol(bld_file, BUILD_ROOT, su.ALL_RULES_KEY)
    cmd = [cc.BUILD_COMMAND, rule_symbol]
    _, builder = cc.generic_core_cmd_handler(cmd, {})
    jar_list.extend(_extract_jar_list(builder))
  return list(set(jar_list))


def _find_bld_files(src_root, include_srcs, exclude_srcs):
  """Find all BLD files we have to build."""
  bld_files = []
  for dir_path, _, files in os.walk(src_root):
    if any([su.child_contained_in(dir_path, d) for d in exclude_srcs]):
      continue
    if include_srcs and not any([su.child_contained_in(dir_path, d)
                                 for d in include_srcs]):
      continue
    bld_files.extend([os.path.join(dir_path, f) for f in files
                      if f == su.BUILD_FILE_NAME])
  return bld_files


def _create_directories(project_dir, src_root):
  """Creates required directories in workspace."""
  if not os.path.exists(project_dir):
    os.mkdir(project_dir)
  link_src = os.path.join(project_dir, os.path.basename(src_root))
  if os.path.islink(link_src):
    if os.path.realpath(link_src) != src_root:
      raise Error('Clean existing project directory {}!'.format(project_dir))
  else:
    os.symlink(src_root, link_src)


def main(program_name, args):
  """Driver function for this extension."""
  args = _parse_command_line(program_name, args)
  workspace_dir = os.environ.get(WORKSPACE_KEY, None) or args.workspace_dir
  if not workspace_dir:
    msg = ('Error: Eclipse workspace directory path not given.'
           ' Recommended to set {} env variable.'.format(WORKSPACE_KEY))
    print msg
    return (1, msg)

  os.chdir(BUILD_ROOT)
  # Make all paths as absolute paths.
  include_srcs = [d if su.child_contained_in(d, BUILD_ROOT)
                  else os.path.join(BUILD_ROOT, d) for d in args.include_srcs]
  exclude_srcs = [d if su.child_contained_in(d, BUILD_ROOT)
                  else os.path.join(BUILD_ROOT, d) for d in args.exclude_srcs]
  src_root = os.path.realpath(args.src_root)
  if not os.path.exists(src_root):
    raise Error('Source root doesn\'t exist!')
  if not su.child_contained_in(src_root, BUILD_ROOT):
    raise Error('Source root must be in BUILD_ROOT!')

  bld_files = _find_bld_files(src_root, include_srcs, exclude_srcs)
  jar_list = _build_all_rules(bld_files)
  os.chdir(BUILD_ROOT)
  # Sort jar list and move jars with sources in the beginning of the list.
  jar_list = sorted(sorted(jar_list, key=lambda x: x[0]),
                    key=lambda x: x[1], reverse=True)

  # Create project directory and eclipse files in workspace.
  project_dir = os.path.join(workspace_dir, args.project_name)
  _create_directories(project_dir, src_root)
  _generate_project_file(project_dir, args.project_name)
  _generate_classpath_file(
      project_dir, include_srcs, exclude_srcs, src_root, jar_list)
  msg = 'Generated .classpath and .project files at %s' % project_dir
  print msg
  return (0, msg)
