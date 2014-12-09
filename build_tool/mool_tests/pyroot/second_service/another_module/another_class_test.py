"""Tests for AnotherClass."""
import pyroot.second_service.another_module.another_class as ac
import pytest


def test_first_func():
  """Test for ac.first_func."""
  assert 42 == ac.first_func()


def test_with_mocking(monkeypatch):
  """Mocked test of ac.first_func."""
  def mock_func():
    """Mocked implementation that is monkey patched."""
    return 22

  monkeypatch.setattr(ac, 'first_func', mock_func)
  assert 22 == ac.first_func()


def test_with_exception():
  """Test with exception."""
  with pytest.raises(ac.Error):
    ac.second_func()
