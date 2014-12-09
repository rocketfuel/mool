"""OneMoreClass implementation."""
import pyroot.first_service.first_module.one_class as oc


def get_value():
  """Get some value."""
  return oc.OneClass.get_value()


def main_func():
  """Some main function."""
  print get_value()
  print 'In main function.'
