"""Format a BLD file."""
import argparse
import os

import mool.shared_utils as su
import utils.bld_parser as bld_parser
import utils.file_utils as fu


def _parse_command_line(program_name, cmd_line):
  """Parse command line to generate arguments."""
  parser = argparse.ArgumentParser(prog=program_name)
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--file', dest='file', help='path to a BLD file',
                     metavar='/project/module/common/BLD')
  group.add_argument('--path', dest='path', metavar='/project/module',
                     help='recursively find & format BLD files in path')
  return parser.parse_args(cmd_line)


def _format_and_write(file_path):
  """Format a given BLD file and write it back."""
  bld_list = bld_parser.bld_to_list(file_path)
  fu.write_file(file_path, bld_parser.list_to_bld_string(bld_list))


def main(program_name, cmd_line):
  """Main entry for BLD pretty formatter."""
  args = _parse_command_line(program_name, cmd_line)
  if args.path:
    count = 0
    for file_path in su.find_all_bld_files(args.path):
      try:
        _format_and_write(file_path)
        print 'Formatted {} file.'.format(file_path)
        count += 1
      except ValueError:
        print "File {} has errors".format(file_path)
  elif args.file:
    count = 1
    _format_and_write(os.path.abspath(args.file))
    print 'Formatted {} file.'.format(args.file)
  return (0, 'Successfully formatted {} BLD files.'.format(count))
