"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

"""

import subprocess
from monnet_gateway.utils.app_context import AppContext
from shared.logger import log

class HostCheckerTask:
    """ Verify known hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
    #    self.hosts = ctx.get_var("known_hosts", [])

    def run(self):
        pass
        #log("Verifying known hosts ...", "debug")
        #for host in self.hosts:
        #    self.check_host(host)

    def ping_host(self, host):
        """ Ping check """
        pass
        #log(f"Ping {host}...", "debug")
        """
        try:
            result = subprocess.run(["ping", "-c", "2", host], capture_output=True, text=True)
            if result.returncode == 0:
                log(f"{host} está en línea.")
            else:
                log(f"{host} no responde.", "warning")
        except Exception as e:
            log(f"Error al comprobar {host}: {e}", "err")
        """
