"""Mool autoupdate script."""
import os
import subprocess

INSTALL_SCRIPT = os.path.join(os.path.dirname(os.environ['BU_SCRIPT_DIR']),
                              'scripts/install_mooltool.py')
PYTHON_BIN = '/usr/bin/python2.7'


def main(_, cmd_line):
  """Main function for update utility."""
  cmd = [PYTHON_BIN, INSTALL_SCRIPT]
  if set(['-h', '--help']).intersection(set(cmd_line)):
    cmd.append('--help')
  else:
    cmd.append('--update')
  subprocess.check_call(cmd)
  return (0,)
