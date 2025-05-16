"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2026 Diego Garcia (diego/@/envigo.net)

Monnet Shared: Logger
"""

import syslog
from monnet_shared.log_level import LogLevel

class Logger:
    def __init__(self, min_log_level: str = "DEBUG", max_stored: int = 200) -> None:
        self.min_log_level = min_log_level
        self.max_stored = max_stored
        self.recent_messages = []

    def set_min_log_level(self, min_log_level: str) -> None:
        """ Set min log level """
        self.min_log_level = min_log_level

    def logpo(self, msg: str, data, priority: str = "INFO") -> None:
        """
        Converts any Python data type to a string and logs it with a specified priority.

        Args:
            msg: A str
            data: The data to log. Can be any Python object.
            priority (str): The priority level (INFO, WARNING, ERROR, CRITICAL).
                            Defaults to 'INFO'.

        Raises:
            ValueError: If the priority level is invalid in the underlying `log` function.
        """
        try:
            message = msg + str(data)  # Convert the data to a string representation
            self.log(message, priority)  # Call the original log function
        except ValueError as e:
            raise ValueError(f"Error in logging: {e}") from e

    def log(self, message: str, priority: str = "INFO") -> None:
        """
        Sends a message to the system log (syslog) with a specified priority.

        Args:
            message (str): The message to log.
            priority (str): The priority level (info, warning, error, critical).
                            Defaults to 'info'.

        Raises:
            ValueError: If the priority level is invalid.
        """
        priority = priority.upper()  # Force uppercase for compatibility
        if priority not in LogLevel.__dict__:
            self.log_error(
                f"Invalid priority level: {priority}. "
                f"Valid options are {list(LogLevel.__dict__.keys()) if '__dict__' in dir(LogLevel) else []}"
            )

        if self.min_log_level.upper() not in LogLevel.__dict__:
            self.log_error(
                f"Invalid MAX_LOG_PRIORITY: {self.min_log_level}. "
                f"Valid options are {list(LogLevel.__dict__.keys()) if '__dict__' in dir(LogLevel) else []}"
            )

        if getattr(LogLevel, priority, None) <= getattr(LogLevel, self.min_log_level.upper(), None):
            syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_USER)
            syslog.syslog(getattr(LogLevel, priority), message)
            self.closelog()
            self._store_message(message, priority)

    def has_stored_logs(self) -> bool:
        """
        Checks if there are any stored logs.

        Returns:
            bool: True if there are stored logs, False otherwise.
        """
        return bool(self.recent_messages)

    def pop_logs(self, num_pop: int = 10) -> list:
        """
        Pops X number of oldest messages

        Args:
            num_pop (int): The number of messages to pop. Defaults to 1.

        Returns:
            list: A list of the oldest log messages.

        """
        if not self.recent_messages:
            return []

        popped_messages = []

        for _ in range(min(num_pop, len(self.recent_messages))):
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
        self.logpo("", message, "INFO")

    def error(self, message: object) -> None:
        """
        Logs an error message.
        """
        self.logpo("", message, "ERROR")

    def err(self, message: object) -> None:
        """
        Logs an error message.
        """
        self.logpo("", message, "ERROR")

    def debug(self, message: object) -> None:
        """
        Logs a debug message.
        """
        self.logpo("", message, "DEBUG")

    def notice(self, message: object) -> None:
        """
        Logs a notice message.
        """
        self.logpo("", message, "NOTICE")

    def warning(self, message: object) -> None:
        """
        Logs a warning message.
        """
        self.logpo("", message, "WARNING")

    def _store_message(self, message: str, priority: str) -> None:
        """
        Stores the message in the recent_messages list, maintaining the size limit.
        Skips storing if the message is identical to the last stored message.

        Args:
            message (str): The message to store.
            priority (str): The priority level of the message.
        """
        priority = priority.upper()  # Ensure priority is uppercase

        # WARN: Store debug messages will raise an exhaust problem when pop logs is called
        if getattr(LogLevel, priority, None) <= LogLevel.NOTICE:
            if self.recent_messages and self.recent_messages[-1]["message"] == message:
                return  # Skip storing if the message is identical to the last one

            truncated_message = message[:255]  # Truncate message to 255 characters for database storage
            self.recent_messages.append({
                "level": getattr(LogLevel, priority, None),
                "message": truncated_message
            })
            if len(self.recent_messages) > self.max_stored:
                self.recent_messages.pop(0)
