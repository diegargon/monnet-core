"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

"""
import subprocess
from shared.app_context import AppContext
from shared.logger import log

class DiscoveryTask:
    """ Descubrimiento de hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.log = ctx.get_logger()
        # self.network_range = ctx.get_var("network_range", "192.168.1.0/24")

    def run(self):
        log("Exec discovery network hosts...", "debug")
        log("Descubrimiento de hosts finalizado.", "debug")
