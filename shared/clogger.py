"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2026 Diego Garcia (diego/@/envigo.net)

Monnet Logger
"""

import syslog

class Logger:
    def __init__(self):
        self.max_log_priority = "debug" # Set the maximum log priority level

    def logpo(self, msg: str, data, priority: str = "info") -> None:
        """
        Converts any Python data type to a string and logs it with a specified priority.

        Args:
            msg: A str
            data: The data to log. Can be any Python object.
            priority (str): The priority level (info, warning, error, critical).
                            Defaults to 'info'.

        Raises:
            ValueError: If the priority level is invalid in the underlying `log` function.
        """
        try:
            message = msg + str(data)  # Convert the data to a string representation
            self.log(message, priority)  # Call the original log function
        except ValueError as e:
            raise ValueError(f"Error in logging: {e}") from e

    def log(self, message: str, priority: str = "info") -> None:
        """
        Sends a message to the system log (syslog) with a specified priority.

        Args:
            message (str): The message to log.
            priority (str): The priority level (info, warning, error, critical).
                            Defaults to 'info'.

        Raises:
            ValueError: If the priority level is invalid.
        """

        syslog_level = {
            "emerg": syslog.LOG_EMERG,
            "alert": syslog.LOG_ALERT,
            "crit": syslog.LOG_CRIT,
            "err": syslog.LOG_ERR,
            "warning": syslog.LOG_WARNING,
            "notice": syslog.LOG_NOTICE,
            "info": syslog.LOG_INFO,
            "debug": syslog.LOG_DEBUG,
        }

        if priority not in syslog_level:
            self.log_error(
                f"Invalid priority level: {priority}. "
                f"Valid options are {list(syslog_level.keys())}"
            )

        if self.max_log_priority not in syslog_level:
            self.log_error(
                f"Invalid MAX_LOG_PRIORITY: {self.max_log_priority}. "
                f"Valid options are {list(syslog_level.keys())}"
            )

        if syslog_level[priority] <= syslog_level[self.max_log_priority]:
            syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
            syslog.syslog(syslog_level[priority], message)
            self.closelog()

    def log_error(self, error_message: str) -> None:
        """
        Logs error messages related to invalid log levels or other critical issues.

        Args:
            error_message (str): The error message to log.
        """
        syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
        syslog.syslog(syslog.LOG_ERR, error_message)
        self.closelog()

    def closelog(self) -> None:
        """
        Close the syslog connection when the daemon shuts down.
        """
        syslog.closelog()
