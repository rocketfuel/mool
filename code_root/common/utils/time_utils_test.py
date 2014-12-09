"""Tests for mool.common.utils.time_utils."""
import common.utils.time_utils as time_utils


def test_get_time_text():
    """Test after init."""
    time_utils.set_timezone()
    assert '1969-12-31 19:00:01' == time_utils.get_time_text(1)
    assert '1969/12/31 19/00' == time_utils.get_time_text(
        1, '%Y/%m/%d %H/%M')


def test_get_epoch_from_text():
    """Test after init."""
    time_utils.set_timezone()
    assert 1 == time_utils.get_epoch_from_text('1969-12-31 19:00:01')
    assert 1 == time_utils.get_epoch_from_text(
        '1969/12/31 19/00/01', '%Y/%m/%d %H/%M/%S')


def test_get_epoch_from_utc_text():
    """Test epoch retrieval from UTC time text."""
    def _test_template(timezone_text):
        """Test these values at a specified timezone."""
        time_utils.set_timezone(timezone_text)
        expected_epoch = 63054001
        assert expected_epoch == time_utils.get_epoch_from_utc_text(
            '1971-12-31 19:00:01', '%Y-%m-%d %H:%M:%S')
        assert expected_epoch == time_utils.get_epoch_from_utc_text(
            '1971-12-31 19:00:01')
        assert expected_epoch == time_utils.get_epoch_from_utc_text(
            '1971/12/31T19:00:01Z', '%Y/%m/%dT%H:%M:%SZ')

    # Test UTC to epoch conversions at different time zones.
    _test_template('US/Alaska')
    _test_template('US/Mountain')
    _test_template(time_utils.STANDARD_TIMEZONE)
