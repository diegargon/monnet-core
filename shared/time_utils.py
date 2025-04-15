"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 -2025 Diego Garcia (diego/@/envigo.net)

Monnet Shared: Time Utilities

"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo  # Replacing pytz

def get_datetime():
    """
    UTC Datetime
    Returns:
        datetime:
    """
    return datetime.now(timezone.utc).isoformat()

def get_local_timezone():
    """
    Timezone
    Returns:
        datetime:
    """
    return datetime.now().astimezone().tzinfo

def date_now(timezone_str='UTC'):
    """
    Get the current date and time in the specified timezone.

    Args:
        timezone_str (str): The timezone string (default is 'UTC').

    Returns:
        str: The current date and time in 'Y-m-d H:M:S' format, or False if the timezone is invalid.
    """
    try:
        tz = ZoneInfo(timezone_str)
    except KeyError:  # ZoneInfo raises KeyError for invalid timezones
        return False

    _date_now = datetime.now(tz)

    return _date_now.strftime('%Y-%m-%d %H:%M:%S')

def utc_date_now():
    """
    Get the current date and time in UTC timezone.

    Returns:
        str: The current date and time in 'Y-m-d H:M:S' format.
    """
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
