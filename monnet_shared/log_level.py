"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Shared: Log Level

Defines constants for log levels in a syslog style format.
"""

class LogLevel:
    """
    Defines constants syslog style

    Log Levels:
        DEBUG: Log level for detailed debugging information.
        INFO: Log level for informational messages.
        NOTICE: Log level for important notifications.
        WARNING: Log level for warning messages indicating potential issues.
        ERROR: Log level for error messages indicating issues that need attention.
        CRITICAL: Log level for critical messages indicating severe issues.
        ALERT: Log level for alerts that require immediate action.
        EMERGENCY: Log level for the most urgent messages indicating system failure.
    """
    DEBUG = 7
    INFO = 6
    NOTICE = 5
    WARNING = 4
    ERROR = 3
    CRITICAL = 2
    ALERT = 1
    EMERGENCY = 0
