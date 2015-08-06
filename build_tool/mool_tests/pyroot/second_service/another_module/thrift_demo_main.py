"""Python module to demo thrift usage."""
import thrift
import some.first.kvpair.constants
import some.first.kvpair.MapService
import some.first.kvpair.ttypes
import some.second.specific.constants
import some.second.specific.SpecificMapService
import some.second.specific.ttypes


def main_func():
  """Entry point."""
  print dir(thrift)
  print dir(some.first.kvpair.constants)
  print dir(some.first.kvpair.MapService)
  print dir(some.first.kvpair.ttypes)
  print
  print dir(some.second.specific.constants)
  print dir(some.second.specific.SpecificMapService)
  print dir(some.second.specific.ttypes)
