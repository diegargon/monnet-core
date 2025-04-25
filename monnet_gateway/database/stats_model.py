"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Stats Model

"""

from monnet_gateway.database.dbmanager import DBManager

class StatsModel:
    def __init__(self, db: DBManager):
        """
        Initialize StatsModel with a database manager.
        Args:
            db: Database manager instance.
        """
        self.db = db

    def add(self, stats_data: dict) -> int:
        """
        Add a new stats record to the database.
        Args:
            stats_data: A dictionary containing 'type', 'host_id', and 'value'.
        Returns:
            The ID of the inserted record.
        """
        return self.db.insert("stats", stats_data)

    def get_by_host_and_date(self, host_id: int, type: int, start_date: str, end_date: str) -> list:
        """
        Retrieve stats records for a specific host and type within a date range.
        Args:
            host_id: The ID of the host.
            type: The type of the stats (e.g., 1 for ping, 2 for load avg, etc.).
            start_date: The start of the date range (inclusive).
            end_date: The end of the date range (inclusive).
        Returns:
            A list of stats records.
        """
        query = """
        SELECT date, type, value
        FROM stats
        WHERE host_id = %s AND type = %s AND date BETWEEN %s AND %s
        ORDER BY date ASC
        """
        params = (host_id, type, start_date, end_date)
        return self.db.fetchall(query, params)

    def get_by_host_last_hours(self, host_id: int, type: int, hours: int = 12) -> list:
        """
        Retrieve stats records for a specific host and type from the last X hours.
        Args:
            host_id: The ID of the host.
            type: The type of the stats (e.g., 1 for ping, 2 for load avg, etc.).
            hours: The number of hours to look back (default is 12).
        Returns:
            A list of stats records.
        """
        query = """
        SELECT date, type, value
        FROM stats
        WHERE host_id = %s AND type = %s AND date >= NOW() - INTERVAL %s HOUR
        ORDER BY date ASC
        """
        params = (host_id, type, hours)
        return self.db.fetchall(query, params)

    def update_stats_bulk(self, stats_data: list[dict]) -> None:
        """
        Update multiple stats records in the database.
        Args:
            stats_data: A list of dictionaries, each containing 'type', 'host_id', 'value', and 'date'.
        """
        query = """
        INSERT INTO stats (type, host_id, value, date)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE value = VALUES(value), date = VALUES(date)
        """
        params = [(stat["type"], stat["host_id"], stat["value"], stat["date"]) for stat in stats_data]
        self.db.executemany(query, params)
        self.db.commit()
