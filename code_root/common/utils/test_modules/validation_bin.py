"""Test module for validating resource reading."""
import common.utils.resource_utils as resource_utils
import common.utils.test_modules.validation_outer as vo


def main_func():
    """Main function."""
    # Validate file packages linked to included library continue working.
    vo.validate_outer()
    # Validate file packages linked directly continue working.
    assert '789' == resource_utils.read_resource('v_resources/file3.txt')
