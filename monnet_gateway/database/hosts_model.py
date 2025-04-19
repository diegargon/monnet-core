"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

from monnet_gateway.database.dbmanager import DBManager

class HostsModel:
    """DB Operations to manage hosts """

    def __init__(self, db: DBManager):
        self.db = db

    def get_all(self) -> list[dict]:
        """ Get all hosts """
        return self.db.fetchall("SELECT * FROM hosts")

    def get_all_enabled(self) -> list[dict]:
        """ Get all hosts enabled """
        return self.db.fetchall("SELECT * FROM hosts WHERE disable = 0")

    def get_by_id(self, host_id: int) -> dict:
        """
        Retrieve a host by its ID.

        Args:
            host_id (int): ID of the host to retrieve.

        Returns:
            dict: A dictionary representing the host, or None if not found.
        """
        query = "SELECT * FROM hosts WHERE id = %s"

        return self.db.fetchone(query, (host_id,))

    def insert_host(self, host: dict) -> int:
        """ Insert a new host """
        columns = ", ".join(host.keys())
        placeholders = ", ".join(["%s"] * len(host))
        values = tuple(host.values())
        query = f"INSERT INTO hosts ({columns}) VALUES ({placeholders})"

        return self.db.execute(query, values)

    def update_host(self, host_id: int, set_data: dict) -> int:
        """
        Update an existing host in the database.

        Args:
            host_id (int): ID of the host to update.
            set_data (dict): Dictionary containing the fields to update.

        Raises:
            ValueError: If set_data is empty.
        """
        if not set_data:
            raise ValueError("No data provided to update the host.")

        columns = ", ".join([f"{key} = %s" for key in set_data.keys()])
        values = tuple(set_data.values())
        query = f"UPDATE hosts SET {columns} WHERE id = %s"

        return self.db.execute(query, values + (host_id,))


    def last_id(self) -> int:
        """ Get last inserted id """
        return self.db.cursor.lastrowid

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
