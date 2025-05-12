"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Networks Model

"""

from monnet_gateway.database.dbmanager import DBManager


class NetworksModel:
    """
    DB Operations to manage networks.

    The `networks` table structure:
    - `id` (Primary, int, AUTO_INCREMENT): Unique identifier for each network.
    - `network` (Index, char(18)): Network address.
    - `name` (Index, char(255), nullable): Name of the network.
    - `vlan` (smallint, nullable): VLAN ID (default is 1).
    - `scan` (tinyint(1)): Scan this network (default is 1).
    - `pool` (tinyint): Pool status (default is 0).
    - `weight` (tinyint): Weight of the network (default is 50).
    - `disable` (tinyint): Disable status (default is 0).
    - `only_online` (tinyint(1)): Show only online host in this network (default is 0).
    - `clean` (tinyint(1)): host "not seen" in this network will be cleared (default is 0).
    """

    def __init__(self, db: DBManager):
        self.db = db

    def get_all(self,) -> list[dict]:
        """ Get all networks """
        return self.db.fetchall("SELECT * FROM networks")

    def get_for_clear(self) -> list[dict]:
        """ Get all networks allowed to clear """
        return self.db.fetchall("SELECT * FROM networks WHERE clean=1")
