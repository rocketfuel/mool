"""Common time utilities."""
import calendar
import os
import time


COMMON_FORMAT_STR = '%Y-%m-%d %H:%M:%S'

# Choosing a standard timezone for demo purposes.
STANDARD_TIMEZONE = 'America/Toronto'


def set_timezone(timezone_text=STANDARD_TIMEZONE):
    """Initializer."""
    os.environ['TZ'] = timezone_text
    time.tzset()


def get_epoch_seconds():
    """Get the number of seconds since Unix epoch."""
    return int(time.time())


def get_time_text(epoch_seconds, format_str=COMMON_FORMAT_STR):
    """Convert seconds since epoch to standard time text.

    Client must call set_timezone before calling this API.
    """
    return time.strftime(format_str, time.localtime(epoch_seconds))


def get_epoch_from_text(time_text, format_str=COMMON_FORMAT_STR):
    """Get seconds since epoch from standard time_text.

    Client must call set_timezone before calling this API.
    """
    return int(time.mktime(time.strptime(time_text, format_str)))


def get_epoch_from_utc_text(utc_text, format_str=COMMON_FORMAT_STR):
    """Get seconds since epoch from UTC time text.

    This method should work correctly independent of time zone.
    """
    return calendar.timegm(time.strptime(utc_text, format_str))
