"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 -2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent

"""

from datetime import datetime, timezone

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
