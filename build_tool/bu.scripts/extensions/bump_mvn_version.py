"""A simple mool extension to bump maven dependency version in a BLD file."""

import argparse
import mool.shared_utils as su
import utils.bld_parser as bp
import utils.file_utils as fu


def _parse_command_line(program_name, cmd_line):
  """Parse command line to generate arguments."""
  parser = argparse.ArgumentParser(prog=program_name)
  parser.add_argument('-r', '--rule_name', type=str,
                      help='build rule name, example HadoopAnnotations')
  parser.add_argument('-a', '--artifact', type=str, default='',
                      help='artifact id, example hadoop-client')
  parser.add_argument('-c', '--classifier', type=str,
                      help='classifier, example source')
  parser.add_argument('-g', '--group', type=str, default='',
                      help='group id, example org.apache.hadoop')
  parser.add_argument('-ov', '--old_version', type=str,
                      help='old version number to update, example 1.2.3')
  parser.add_argument('-f', '--bld_file', type=str, required=True,
                      help='full path to BLD file to update')
  parser.add_argument('-nv', '--new_version', type=str, required=True,
                      help='new version number to set, example 1.2.3')
  return parser.parse_args(cmd_line)


def main(program_name, cmd_line):
  """Main function for this module."""
  args = _parse_command_line(program_name, cmd_line)
  match_indexes = []
  bld_list = bp.bld_to_list(args.bld_file)

  for index in xrange(len(bld_list)):
    item = bld_list[index]
    if isinstance(item, dict):
      if su.MAVEN_SPECS_KEY in item[bp.RULE_BODY_KEY]:
        specs = item[bp.RULE_BODY_KEY][su.MAVEN_SPECS_KEY]
        match = any([
            item[bp.RULE_NAME_KEY] == args.rule_name,
            all([args.rule_name is None,
                 specs[su.MAVEN_ARTIFACT_ID_KEY] == args.artifact,
                 specs[su.MAVEN_GROUP_ID_KEY] == args.group,
                 (args.classifier is None or
                  specs.get(su.MAVEN_CLASSIFIER_KEY, '') == args.classifier),
                 (args.old_version is None or
                  specs[su.MAVEN_VERSION_KEY] == args.old_version)])])
        if match:
          match_indexes.append(index)

  if len(match_indexes) == 0:
    raise su.Error('Couldn\'t find requested build rule in {} file.'.format(
                   args.bld_file))
  if len(match_indexes) > 1:
    raise su.Error('Update failed, more than 1 matches found. '
                   'Provide more info!!')
  index = match_indexes[0]
  rule_body = bld_list[index][bp.RULE_BODY_KEY]
  old_version = rule_body[su.MAVEN_SPECS_KEY][su.MAVEN_VERSION_KEY]
  rule_body[su.MAVEN_SPECS_KEY][su.MAVEN_VERSION_KEY] = args.new_version
  bld_list[index][bp.RULE_BODY_KEY] = rule_body
  fu.write_file(args.bld_file, bp.list_to_bld_string(bld_list))
  msg = 'Successfully update version from {} to {}'.format(old_version,
                                                           args.new_version)
  return (0, msg)
