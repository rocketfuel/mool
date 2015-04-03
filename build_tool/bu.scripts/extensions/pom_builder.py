"""A quick script to generate maven compatible pom.xml file from given build
rule."""

from xml.dom import minidom
import argparse
import json
import logging
import os
import xml.etree.ElementTree as ET

import mool.core_cmds as cc
import mool.shared_utils as su

DEFAULT_POM_FILE = 'pom.xml'


class Error(su.Error):
  """Error class for this module."""


def _parse_command_line(program_name, cmd_line):
  """Command line arguments parser."""
  arg_parser = argparse.ArgumentParser(prog=program_name)
  arg_parser.add_argument('-g', '--group', type=str, default='',
                          help='group id, example org.apache.hadoop')
  arg_parser.add_argument('-a', '--artifact', type=str, default='',
                          help='artifact id, example hadoop-client')
  arg_parser.add_argument('-v', '--version', type=str, default='',
                          help='version number, example 1.2.3')
  arg_parser.add_argument('-r', '--build_rule', type=str, required=True,
                          help='java build rule to generate pom from')
  pom_file = os.path.abspath(os.path.join('.', DEFAULT_POM_FILE))
  arg_parser.add_argument('-o', '--pom_path', type=str, default=pom_file,
                          help='full path to output pom.xml file')
  return arg_parser.parse_args(cmd_line)


def _validate_helper(dict_obj, key, alternative):
  """Validate that one of the given parameters is valid. Print a pretty
  message on failure."""
  if key not in dict_obj and not alternative:
    raise Error('Unable to determine value of {}!'.format(key))
  return alternative or dict_obj[key]


def _get_dependency_elem(dep_dict):
  """Returns a dependency element from given dictionary."""
  elem = ET.Element('dependency')
  # TODO: Move these constants to some common file.
  keys = ['groupId', 'artifactId', 'version', 'classifier', 'scope']
  for key in keys:
    if dep_dict[key]:
      elem.append(_get_data_element(key, dep_dict[key]))
  return elem


def _get_data_element(tag, data):
  """Returns an element with given tag and text body."""
  elem = ET.Element(tag)
  elem.text = data
  return elem


def _get_repositories_element(repo_set):
  """Returns the set of repositories formatted in pom format."""
  repositories = ET.Element('repositories')
  counter = 0
  for repo in repo_set:
    counter = counter + 1
    elem = ET.Element('repository')
    elem.append(_get_data_element('id', 'repo{}'.format(counter)))
    elem.append(_get_data_element('name', 'Repository {}'.format(counter)))
    elem.append(_get_data_element('layout', 'default'))
    elem.append(_get_data_element('url', repo))
    repositories.append(elem)
  return repositories


def _generate_pom_file(args, deps_file):
  """Generate pom file from given JSON file having all the dependency
  details."""
  with open(deps_file, 'r') as deps_file_obj:
    data = json.load(deps_file_obj)

  # Collect project specific information.
  group_id = _validate_helper(data, 'groupId', args.group)
  artifact_id = _validate_helper(data, 'artifactId', args.artifact)
  version = _validate_helper(data, 'version', args.version)

  root = ET.Element('project', xmlns='http://maven.apache.org/POM/4.0.0')
  root.append(_get_data_element('modelVersion', '4.0.0'))
  root.append(_get_data_element('groupId', group_id))
  root.append(_get_data_element('artifactId', artifact_id))
  root.append(_get_data_element('version', version))
  root.append(_get_data_element('packaging', 'jar'))
  dependencies = ET.Element('dependencies')
  repo_set = set()
  for dep in data.get('deps', []):
    dependencies.append(_get_dependency_elem(dep))
    repo_set.add(dep['repoUrl'])

  # Dump the xml to given file.
  root.append(dependencies)
  root.append(_get_repositories_element(repo_set))
  xml_string = ET.tostring(root, encoding='utf-8', method='xml')
  with open(args.pom_path, 'w') as pom_obj:
    pom_obj.write(minidom.parseString(xml_string).toprettyxml(indent='  '))


def main(program_name, cmd_line):
  """Main function to trigger rule building and its pom generation."""
  args = _parse_command_line(program_name, cmd_line)
  ret_code, builder = cc.generic_core_cmd_handler(
      [cc.BUILD_COMMAND, args.build_rule], {})
  if ret_code != 0:
    msg = 'Error building rule %s!', args.build_rule
    logging.error(msg)
    return (1, msg)
  rule_details = builder.get_rules_map()[args.build_rule]
  deps_file_path = rule_details[su.EXPORTED_MVN_DEPS_FILE_KEY]
  _generate_pom_file(args, deps_file_path)
  msg = 'Successfully created {}.'.format(args.pom_path)
  logging.info(msg)
  return (0, msg)
