"""Test library for validating resource reading (inner module)."""
import common.utils.resource_utils as resource_utils


def validate_inner():
    """Load resource from current library and validate."""
    assert '0000' == resource_utils.read_resource('v_resources/file0.txt')
