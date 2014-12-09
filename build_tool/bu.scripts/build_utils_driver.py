#!/usr/bin/env python2.7
"""Utilities for build project."""
import os
import sys

if __name__ == '__main__':
  SCRIPT_DIR = os.path.dirname(sys.argv[0])
  if SCRIPT_DIR != sys.path[0]:
    sys.path.insert(0, SCRIPT_DIR)

import build_utils as bu

if __name__ == '__main__':
  sys.exit(bu.do_main(sys.argv[1:]))
