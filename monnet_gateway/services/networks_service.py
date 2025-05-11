"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Networks Service

"""

from monnet_gateway.database.networks_model import NetworksModel

class NetworksService:
    def __init__(self, networks_model: NetworksModel):
        self.networks_model = networks_model

    def get_all(self) -> list[dict]:
        """ Get all networks """
        return self.networks_model.get_all()

    def get_networks_for_clear(self) -> list[dict]:
        """ Get all networks where clear=1 """
        return self.networks_model.get_for_clear()
