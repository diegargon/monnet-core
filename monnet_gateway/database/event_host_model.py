"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Event Log Service

"""

from monnet_gateway.database.dbmanager import DBManager


class EventHostModel:
    """
    Handles operations related to the `hosts_logs` table.

    The `hosts_logs` table structure:
    - `id` (Primary, int, AUTO_INCREMENT): Unique identifier for each log entry.
    - `host_id` (Index, int): ID of the host associated with the log entry.
    - `level` (Index, tinyint): Severity level of the log (default is 7).
    - `log_type` (varchar(255)): Type of the log (DEFAULT = 0, EVENT = 1, EVENT_WARN = 2, EVENT_ALERT = 3).
    - `event_type` (smallint, nullable): Type of the event (default is 0).
    - `msg` (char(255)): Message or description of the log.
    - `ack` (tinyint(1)): Acknowledgment status (0 = not acknowledged, 1 = acknowledged).
    - `date` (Index, datetime): Timestamp of the log entry.
    - 'tid' int task id for events trigger
    """

    def __init__(self, db: DBManager):
        """
        Initialize EventLogModel with a database manager.

        Args:
            db: Database manager instance.
        """
        self.db = db

    def insert_event(self, log_data: dict) -> int:
        """
        Insert a new log entry into the `hosts_logs` table.

        Args:
            log_data (dict): Dictionary containing log details.

        Returns:
            int: ID of the newly inserted log entry.
        """
        return self.db.insert("hosts_logs", log_data)

    def commit(self) -> None:
        """
        Commit changes to the database.
        """
        self.db.commit()