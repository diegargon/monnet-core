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
