"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Networks Service

"""

from monnet_gateway.database.dbmanager import DBManager
from monnet_gateway.database.networks_model import NetworksModel
from monnet_shared.app_context import AppContext

class NetworksService:
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        self.config = ctx.get_config()
        self.db = DBManager(self.config)
        self.networks_model = NetworksModel(self.db)

    def get_all(self) -> list[dict]:
        """ Get all networks """
        return self.networks_model.get_all()

    def get_networks_for_clear(self) -> list[dict]:
        """ Get all networks where clear=1 """
        return self.networks_model.get_for_clear()
