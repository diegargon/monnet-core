"""
@copyright CC BY-NC-ND 4.0 @ 2020 - 2025 Diego Garcia (diego/@/envigo.net)

"""

from shared.app_context import AppContext

class HostsCheckerTask:
    """ Verify known hosts """
    def __init__(self, ctx: AppContext):
        self.ctx = ctx
        self.logger = ctx.get_logger()
    #    self.hosts = ctx.get_var("known_hosts", [])

    def run(self):
        self.logger.debug("Verifying known hosts ...")

    def ping_host(self, host):
        """ Ping check """
        self.logger.debug(f"Ping {host}...")
