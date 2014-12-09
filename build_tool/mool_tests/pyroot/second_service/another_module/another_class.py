"""AnotherClass implementation."""
import pyroot.first_service.first_module.one_class as oc


class Error(Exception):
  """The Exception class for this module."""


def first_func():
  """First function call."""
  return 42


def second_func():
  """Second function call."""
  raise Error('Some error.')


def main_func():
  """Some main function."""
  print first_func()
  print oc.OneClass().get_special()
  print 'In second module main function.'
