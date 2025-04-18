"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2026 Diego Garcia (diego/@/envigo.net)

Monnet Shared: Logger
"""

import syslog
from constants.log_level import SYSLOG_LEVELS

class Logger:
    def __init__(self, min_log_level: str = "debug", max_stored: int = 200) -> None:
        self.min_log_level = min_log_level
        self.max_stored = max_stored
        self.recent_messages = []

    def set_min_log_level(self, min_log_level: str) -> None:
        """ Set min log level """
        self.min_log_level = min_log_level

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
        if priority not in SYSLOG_LEVELS:
            self.log_error(
                f"Invalid priority level: {priority}. "
                f"Valid options are {list(SYSLOG_LEVELS.keys())}"
            )

        if self.min_log_level not in SYSLOG_LEVELS:
            self.log_error(
                f"Invalid MAX_LOG_PRIORITY: {self.min_log_level}. "
                f"Valid options are {list(SYSLOG_LEVELS.keys())}"
            )

        if SYSLOG_LEVELS[priority] <= SYSLOG_LEVELS[self.min_log_level]:
            syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
            syslog.syslog(SYSLOG_LEVELS[priority], message)
            self.closelog()
            self._store_message(message, priority)

    def has_stored_logs(self) -> bool:
        """
        Checks if there are any stored logs.

        Returns:
            bool: True if there are stored logs, False otherwise.
        """
        return bool(self.recent_messages)

    def pop_logs(self, count: int = 1) -> list:
        """
        Pops X number of oldest messages

        Args:
            count (int): The number of messages to pop. Defaults to 1.

        Returns:
            list: A list of the oldest log messages.

        """
        if not self.recent_messages:
            return []

        popped_messages = []

        for _ in range(min(count, len(self.recent_messages))):
            popped_messages.append(self.recent_messages.pop(0))

        return popped_messages

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

    def info(self, message: object) -> None:
        """
        Logs an informational message.
        """
        self.logpo("", message, "info")

    def error(self, message: object) -> None:
        """
        Logs an error message.
        """
        self.logpo("", message, "err")

    def err(self, message: object) -> None:
        """
        Logs an error message.
        """
        self.logpo("", message, "err")

    def debug(self, message: object) -> None:
        """
        Logs a debug message.
        """
        self.logpo("", message, "debug")

    def notice(self, message: object) -> None:
        """
        Logs a notice message.
        """
        self.logpo("", message, "notice")

    def warning(self, message: object) -> None:
        """
        Logs a warning message.
        """
        self.logpo("", message, "warning")

    def _store_message(self, message: str, priority: str) -> None:
        """
        Stores the message in the recent_messages list, maintaining the size limit.

        Args:
            message (str): The message to store.
            priority (str): The priority level of the message.
        """

        # WARN: Store debug messages will raise an exhaust problem when pop logs is called
        if SYSLOG_LEVELS[priority] <= syslog.LOG_NOTICE:
            self.recent_messages.append({
                "level": SYSLOG_LEVELS[priority],
                "message": message
            })
            if len(self.recent_messages) > self.max_stored:
                self.recent_messages.pop(0)
