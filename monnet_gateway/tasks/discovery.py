"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

"""
import subprocess
from monnet_gateway.utils.context import AppContext
from shared.logger import log

class DiscoveryTask:
    """ Descubrimiento de hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        # self.network_range = ctx.get_var("network_range", "192.168.1.0/24")

    def run(self):
        log("Exec discovery network hosts...", "debug")
        """
        try:
            result = subprocess.run(["monnet-cli", "--discover", self.network_range], capture_output=True, text=True)
            log(f"Resultado del descubrimiento: {result.stdout}")
        except Exception as e:
            log(f"Error en DiscoveryTask: {e}", "error")
        """
        log("Descubrimiento de hosts finalizado.", "debug")
