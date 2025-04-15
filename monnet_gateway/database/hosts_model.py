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

    def insert_host(self, host: dict) -> int:
        """ Insert a new host """
        columns = ", ".join(host.keys())
        placeholders = ", ".join(["%s"] * len(host))
        values = tuple(host.values())
        query = f"INSERT INTO hosts ({columns}) VALUES ({placeholders})"
        self.db.execute(query, values)
        self.db.commit()
        return self.db.cursor.lastrowid