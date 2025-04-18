"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway - Ports Service

"""

from monnet_gateway.database.ports_model import PortsModel
from shared.app_context import AppContext


class PortsService:
    """ Ports service """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.db = ctx.get_database()
        self.ports_model = PortsModel(self.db)

    def update_ports(self, ports_data: list[dict]):
        self.ports_model.update_ports(ports_data)
        self.ports_model.commit()

    def get_host_ports(self, hid: int, scan_type: int = None) -> dict:
        """ Get ports by host id """
        return self.ports_model.get_by_hid(hid, scan_type)
