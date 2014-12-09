"""OneClass implementation."""


class OneClass(object):
  """The implementation of OneClass."""
  def __init__(self):
    """Initializer."""
    self.value = 23

  @classmethod
  def get_value(cls):
    """Get per-class value."""
    return 1

  def get_special(self):
    """Get per-object value."""
    return self.value
