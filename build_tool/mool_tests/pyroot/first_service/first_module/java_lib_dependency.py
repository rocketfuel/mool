"""Python script to test if python binary can have java library dependencies.
"""

import os

RELATIVE_PATH = 'clickstream/clickstream/1.0.2/clickstream-1.0.2-sources.jar'
JAR_PATH = os.path.join(os.environ['JAR_SEARCH_PATH'], RELATIVE_PATH)


def main():
  """Just check if the dependent JAR file exists in expected path."""
  assert os.path.exists(JAR_PATH)
  print 'Test Passed: Clickstream JAR Exists!'
