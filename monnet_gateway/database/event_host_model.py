"""
@copyright Copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Event Log Service

"""

from monnet_gateway.database.dbmanager import DBManager


class EventHostModel:
    """
    Handles operations related to the `hosts_logs` table.
    """

    def __init__(self, db_manager: DBManager):
        """
        Initialize EventLogModel with a database manager.

        Args:
            db: Database manager instance.
        """
        self.db = db_manager

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
            Commit changes
        """
        self.db.commit()