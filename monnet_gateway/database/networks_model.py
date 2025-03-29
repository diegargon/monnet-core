"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

from monnet_gateway.database.dbmanager import DBManager


class NetworksModel:
    """DB Operations to manage networks"""

    def __init__(self, db: DBManager):
        self.db = db

    def get_all(self,) -> list[dict]:
        """ Get all networks """
        return self.db.fetchall("SELECT * FROM networks")
