"""End-to-end tests for pyroot.first_service.first_module."""
import pyroot.first_service.first_module.one_class as oc
import pyroot.first_service.first_module.one_more_class as omc


def test_get_value():
  """Test for the get_value function."""
  assert 1 == omc.get_value()


def test_get_special():
  """Tests for oc.get_special."""
  assert 23 == oc.OneClass().get_special()
