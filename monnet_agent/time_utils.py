"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 -2025 Diego Garcia (diego/@/envigo.net)

Monnet Agent
"""

from datetime import datetime, timezone


def get_datatime():
    """
    UTC Datetime
    Returns:
        datatime:
    """
    return datetime.now(timezone.utc).isoformat()

def get_local_timezone():
    """
    Timezone
    Returns:
        datatime:
    """
    return datetime.now().astimezone().tzinfo
