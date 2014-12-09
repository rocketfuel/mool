"""Test library for validating resource reading (outer module)."""
import common.utils.resource_utils as resource_utils
import common.utils.test_modules.validation_inner as vi


def validate_outer():
    """Load resource from current library and validate."""
    vi.validate_inner()
    assert '123' == resource_utils.read_resource('v_resources/file1.txt')
    assert '456' == resource_utils.read_resource('v_resources/file2.txt')
