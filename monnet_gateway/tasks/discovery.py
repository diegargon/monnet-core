"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

Monnet Gateway

"""

from shared.app_context import AppContext

class DiscoveryHostsTask:
    """ Descubrimiento de hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
        # self.network_range = ctx.get_var("network_range", "192.168.1.0/24")

    def run(self):
        self.logger.debug("Exec discovery network hosts...")
        self.logger.debug("Descubrimiento de hosts finalizado.")
